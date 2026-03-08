"""
Backup management endpoints
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset, DataFile
from app.models.task import Task, TaskStatus, TaskType
from app.schemas import TaskResponse, MessageResponse
from app.services.backup import backup_service

router = APIRouter(prefix="/backups", tags=["backups"])


class BackupRequest(BaseModel):
    backup_type: str = "full"  # full, incremental
    description: Optional[str] = None


class RestoreRequest(BaseModel):
    target_dataset_id: Optional[int] = None  # If None, restore to original


@router.post("/datasets/{dataset_id}", response_model=dict)
async def create_backup(
    dataset_id: int,
    request: BackupRequest = BackupRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a backup of a dataset."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    result = await db.execute(
        select(DataFile).where(DataFile.dataset_id == dataset_id)
    )
    files = result.scalars().all()
    
    try:
        backup_info = await backup_service.create_backup(
            dataset=dataset,
            files=files,
            backup_type=request.backup_type,
            description=request.description,
        )
        return backup_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_backups(
    dataset_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """List all backups."""
    backups = backup_service.list_backups(dataset_id)
    return {"backups": backups}


@router.get("/{backup_name}")
async def get_backup_info(
    backup_name: str,
    current_user: User = Depends(get_current_user),
):
    """Get info about a specific backup."""
    info = backup_service.get_backup_info(backup_name)
    if not info:
        raise HTTPException(status_code=404, detail="Backup not found")
    return info


@router.post("/{backup_name}/restore")
async def restore_backup(
    backup_name: str,
    request: RestoreRequest = RestoreRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore a dataset from backup."""
    backup_info = backup_service.get_backup_info(backup_name)
    if not backup_info:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    # Get target dataset
    target_id = request.target_dataset_id or backup_info["dataset_id"]
    result = await db.execute(
        select(Dataset).where(Dataset.id == target_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Target dataset not found")
    
    try:
        result = await backup_service.restore_backup(backup_name, dataset)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{backup_name}")
async def delete_backup(
    backup_name: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a backup."""
    if backup_service.delete_backup(backup_name):
        return {"message": "Backup deleted"}
    raise HTTPException(status_code=404, detail="Backup not found")


@router.post("/prune")
async def prune_backups(
    keep_count: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Prune old backups, keeping only the most recent ones."""
    deleted = await backup_service.prune_old_backups(keep_count)
    return {
        "deleted": deleted,
        "deleted_count": len(deleted),
        "message": f"Deleted {len(deleted)} old backups"
    }


@router.get("/size")
async def get_backup_size(
    current_user: User = Depends(get_current_user),
):
    """Get total backup size."""
    size = backup_service.get_backup_size()
    return {
        "size_bytes": size,
        "size_human": _format_size(size)
    }


def _format_size(bytes: int) -> str:
    if bytes < 1024:
        return f"{bytes} B"
    if bytes < 1024 * 1024:
        return f"{bytes / 1024:.1f} KB"
    if bytes < 1024 * 1024 * 1024:
        return f"{bytes / 1024 / 1024:.1f} MB"
    return f"{bytes / 1024 / 1024 / 1024:.2f} GB"
