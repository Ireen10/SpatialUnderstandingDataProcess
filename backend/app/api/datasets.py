"""
Dataset management endpoints
"""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
import asyncio

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset, DataFile, DataStatus
from app.models.task import Task, TaskStatus, TaskType
from app.schemas import (
    DatasetCreate, DatasetUpdate, DatasetResponse,
    DataFileResponse, DataFileWithMetadata, PaginatedResponse, MessageResponse,
    TaskResponse,
)
from app.services.download import download_service
from app.services.metadata import metadata_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=PaginatedResponse)
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's datasets."""
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
    """Create a new dataset."""
    dataset = Dataset(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        storage_path=data.storage_path,
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


@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: int,
    data: DatasetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update dataset."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if data.name is not None:
        dataset.name = data.name
    if data.description is not None:
        dataset.description = data.description
    
    await db.commit()
    await db.refresh(dataset)
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete dataset and its files."""
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
    
    # Delete files from storage
    storage_path = Path(settings.DATA_STORAGE_PATH) / dataset.storage_path
    if storage_path.exists():
        import shutil
        print(f"[DELETE] Removing storage path: {storage_path}")
        shutil.rmtree(storage_path, ignore_errors=True)
    else:
        print(f"[DELETE WARNING] Storage path does not exist: {storage_path}")
    
    # Delete associated DataFile records first (cascade should handle this, but be explicit)
    from app.models.dataset import DataFile
    await db.execute(
        delete(DataFile).where(DataFile.dataset_id == dataset_id)
    )
    
    await db.delete(dataset)
    await db.commit()
    print(f"[DELETE SUCCESS] Dataset {dataset_id} '{dataset.name}' deleted")


@router.get("/{dataset_id}/files", response_model=PaginatedResponse)
async def list_dataset_files(
    dataset_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List files in a dataset."""
    # Verify ownership
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Build query
    query = select(DataFile).where(DataFile.dataset_id == dataset_id)
    count_query = select(func.count(DataFile.id)).where(DataFile.dataset_id == dataset_id)
    
    if status_filter:
        query = query.where(DataFile.status == status_filter)
        count_query = count_query.where(DataFile.status == status_filter)
    
    # Count total
    total = (await db.execute(count_query)).scalar()
    
    # Get paginated results
    result = await db.execute(
        query.order_by(DataFile.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    files = result.scalars().all()
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[DataFileResponse.model_validate(f) for f in files],
    )


@router.get("/{dataset_id}/files/{file_id}", response_model=DataFileWithMetadata)
async def get_dataset_file(
    dataset_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get file details with metadata."""
    # Verify ownership
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    result = await db.execute(
        select(DataFile)
        .options(selectinload(DataFile.file_metadata))
        .where(DataFile.id == file_id, DataFile.dataset_id == dataset_id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    response = DataFileWithMetadata.model_validate(file)
    if file.file_metadata:
        response.metadata = {
            "width": file.file_metadata.width,
            "height": file.file_metadata.height,
            "duration": file.file_metadata.duration,
            "fps": file.file_metadata.fps,
            "text_length": file.file_metadata.text_length,
            "word_count": file.file_metadata.word_count,
        }
    return response


@router.post("/{dataset_id}/download/huggingface", response_model=TaskResponse)
async def download_from_huggingface(
    dataset_id: int,
    repo_id: str = Query(..., description="HuggingFace repo ID"),
    allow_patterns: Optional[str] = Query(None, description="Comma-separated patterns to include"),
    ignore_patterns: Optional[str] = Query(None, description="Comma-separated patterns to exclude"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download dataset from HuggingFace Hub."""
    # Verify ownership
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Create task
    task = Task(
        user_id=current_user.id,
        task_type=TaskType.DOWNLOAD.value,
        name=f"Download HF: {repo_id}",
        input_params={
            "repo_id": repo_id,
            "allow_patterns": allow_patterns.split(",") if allow_patterns else None,
            "ignore_patterns": ignore_patterns.split(",") if ignore_patterns else None,
        },
        dataset_id=dataset_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # Run download in background (will be handled by Celery in production)
    # For now, we'll use asyncio
    asyncio.create_task(_run_download(task.id, dataset.id, repo_id, allow_patterns, ignore_patterns))
    
    return task


@router.post("/{dataset_id}/download/url", response_model=TaskResponse)
async def download_from_url(
    dataset_id: int,
    url: str = Query(..., description="Download URL"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download file from URL."""
    # Verify ownership
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Create task
    task = Task(
        user_id=current_user.id,
        task_type=TaskType.DOWNLOAD.value,
        name=f"Download: {url[:50]}...",
        input_params={"url": url},
        dataset_id=dataset_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # Run download in background
    asyncio.create_task(_run_url_download(task.id, dataset.id, url))
    
    return task


@router.post("/{dataset_id}/scan", response_model=MessageResponse)
async def scan_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Scan storage path and update file index."""
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


# Background task handlers
async def _run_download(task_id: int, dataset_id: int, repo_id: str, allow_patterns: str = None, ignore_patterns: str = None):
    """Background task for HuggingFace download."""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one()
            
            result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
            dataset = result.scalar_one()
            
            await download_service.download_from_huggingface(
                repo_id=repo_id,
                dataset=dataset,
                task=task,
                allow_patterns=allow_patterns.split(",") if allow_patterns else None,
                ignore_patterns=ignore_patterns.split(",") if ignore_patterns else None,
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"Download task failed: {e}")


async def _run_url_download(task_id: int, dataset_id: int, url: str):
    """Background task for URL download."""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one()
            
            result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
            dataset = result.scalar_one()
            
            await download_service.download_from_url(url=url, dataset=dataset, task=task)
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"URL download task failed: {e}")
