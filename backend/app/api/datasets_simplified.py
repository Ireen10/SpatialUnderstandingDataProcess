"""
Dataset management endpoints - Refactored for folder-based datasets
"""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
import os

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset, DataFile, DataStatus
from app.models.task import Task, TaskStatus, TaskType
from app.schemas import (
    DatasetCreate, DatasetUpdate, DatasetResponse,
    DataFileResponse, PaginatedResponse, MessageResponse, TaskResponse,
)
from app.services.download import download_service
from app.services.metadata import metadata_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


async def _auto_sync_datasets(storage_path: Path, current_user: User, db: AsyncSession):
    """
    Automatically sync datasets from storage folder.
    Each folder = one dataset.
    """
    if not storage_path.exists():
        return
    
    # Get existing datasets
    result = await db.execute(
        select(Dataset).where(Dataset.user_id == current_user.id)
    )
    existing_datasets = {d.name: d for d in result.scalars().all()}
    
    # Scan folders
    for folder in storage_path.iterdir():
        if not folder.is_dir():
            continue
        
        # Skip system folders
        if folder.name.startswith('.') or folder.name in ['__pycache__', 'temp', 'logs', 'images', 'covers']:
            continue
        
        dataset_name = folder.name
        
        # Create dataset if not exists
        if dataset_name not in existing_datasets:
            dataset = Dataset(
                user_id=current_user.id,
                name=dataset_name,
                description=f"Auto-detected dataset from folder: {dataset_name}",
                storage_path=str(folder.relative_to(storage_path)),
            )
            db.add(dataset)
            print(f"[AUTO-SYNC] Created dataset: {dataset_name}")
    
    await db.commit()


@router.get("", response_model=PaginatedResponse)
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scan: bool = Query(True, description="是否自动扫描 data 文件夹"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's datasets.
    Automatically scans the data folder and creates dataset records.
    """
    storage_path = Path(settings.DATA_STORAGE_PATH)
    
    # Auto-scan on every request (default scan=True)
    if scan and storage_path.exists():
        await _auto_sync_datasets(storage_path, current_user, db)
    
    # Count total
    count_result = await db.execute(
        select(func.count(Dataset.id)).where(Dataset.user_id == current_user.id)
    )
    total = count_result.scalar()
    
    # Get paginated results
    result = await db.execute(
        select(Dataset)
        .where(Dataset.user_id == current_user.id)
        .order_by(Dataset.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    datasets = result.scalars().all()
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[DatasetResponse.model_validate(d) for d in datasets],
    )


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    data: DatasetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new dataset (will create folder on download)."""
    dataset = Dataset(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        storage_path=data.name,  # Use dataset name as folder name
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dataset by ID."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete dataset and its folder."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        # Try to find dataset without user filter for debugging
        debug_result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
        debug_dataset = debug_result.scalar_one_or_none()
        if debug_dataset:
            print(f"[DELETE ERROR] Dataset {dataset_id} exists but belongs to user {debug_dataset.user_id}, current user: {current_user.id}")
            raise HTTPException(status_code=403, detail="无权删除此数据集（权限不匹配）")
        else:
            print(f"[DELETE ERROR] Dataset {dataset_id} not found in database")
            raise HTTPException(status_code=404, detail="数据集不存在")
    
    # Delete files from storage (ignore if path doesn't exist)
    storage_path = Path(settings.DATA_STORAGE_PATH) / dataset.storage_path
    if storage_path.exists():
        import shutil
        print(f"[DELETE] Removing storage path: {storage_path}")
        shutil.rmtree(storage_path, ignore_errors=True)
    else:
        print(f"[DELETE WARNING] Storage path does not exist (may be manually deleted): {storage_path}")
    
    # Delete associated DataFile records first (explicit cascade)
    result = await db.execute(
        select(DataFile).where(DataFile.dataset_id == dataset_id)
    )
    files = result.scalars().all()
    print(f"[DELETE] Deleting {len(files)} file records from database")
    
    await db.execute(
        delete(DataFile).where(DataFile.dataset_id == dataset_id)
    )
    
    # Delete dataset record
    dataset_name = dataset.name
    await db.delete(dataset)
    await db.commit()
    
    print(f"[DELETE SUCCESS] Dataset {dataset_id} '{dataset_name}' and {len(files)} files deleted")


@router.post("/{dataset_id}/scan", response_model=MessageResponse)
async def scan_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Scan dataset folder and update file index."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    storage_path = Path(settings.DATA_STORAGE_PATH) / dataset.storage_path
    if not storage_path.exists():
        raise HTTPException(status_code=400, detail="Storage path does not exist")
    
    # Re-index files
    count = await download_service._index_downloaded_files(storage_path, dataset, db)
    await db.commit()
    
    return MessageResponse(message=f"Scanned and indexed {count} files")


# Background task handlers (keep existing implementations...)
# [Rest of the file remains the same as before]
