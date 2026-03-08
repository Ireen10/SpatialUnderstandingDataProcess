"""
Statistics endpoints for data insights
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset, DataFile, DataType, DataStatus
from app.models.task import Task, TaskStatus, TaskType

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/overview")
async def get_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get overview statistics for user's data."""
    # Total datasets
    datasets_result = await db.execute(
        select(func.count(Dataset.id)).where(Dataset.user_id == current_user.id)
    )
    total_datasets = datasets_result.scalar()
    
    # Total files
    files_result = await db.execute(
        select(func.count(DataFile.id))
        .join(Dataset)
        .where(Dataset.user_id == current_user.id)
    )
    total_files = files_result.scalar()
    
    # Total size
    size_result = await db.execute(
        select(func.sum(DataFile.file_size))
        .join(Dataset)
        .where(Dataset.user_id == current_user.id)
    )
    total_size = size_result.scalar() or 0
    
    # Files by type
    type_result = await db.execute(
        select(DataFile.data_type, func.count(DataFile.id).label("count"))
        .join(Dataset)
        .where(Dataset.user_id == current_user.id)
        .group_by(DataFile.data_type)
    )
    files_by_type = {row.data_type: row.count for row in type_result}
    
    # Files by status
    status_result = await db.execute(
        select(DataFile.status, func.count(DataFile.id).label("count"))
        .join(Dataset)
        .where(Dataset.user_id == current_user.id)
        .group_by(DataFile.status)
    )
    files_by_status = {row.status: row.count for row in status_result}
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_files = await db.execute(
        select(func.count(DataFile.id))
        .join(Dataset)
        .where(
            Dataset.user_id == current_user.id,
            DataFile.created_at >= week_ago
        )
    )
    new_files_week = recent_files.scalar()
    
    # Tasks summary
    pending_tasks = await db.execute(
        select(func.count(Task.id))
        .where(Task.user_id == current_user.id, Task.status == TaskStatus.PENDING.value)
    )
    running_tasks = await db.execute(
        select(func.count(Task.id))
        .where(Task.user_id == current_user.id, Task.status == TaskStatus.RUNNING.value)
    )
    
    return {
        "total_datasets": total_datasets,
        "total_files": total_files,
        "total_size": total_size,
        "files_by_type": files_by_type,
        "files_by_status": files_by_status,
        "new_files_week": new_files_week,
        "pending_tasks": pending_tasks.scalar(),
        "running_tasks": running_tasks.scalar(),
    }


@router.get("/timeline")
async def get_timeline(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get file addition timeline."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Group by date
    result = await db.execute(
        select(
            func.date(DataFile.created_at).label("date"),
            func.count(DataFile.id).label("count"),
            func.sum(DataFile.file_size).label("size")
        )
        .join(Dataset)
        .where(
            Dataset.user_id == current_user.id,
            DataFile.created_at >= start_date
        )
        .group_by(func.date(DataFile.created_at))
        .order_by(func.date(DataFile.created_at))
    )
    
    timeline = [
        {
            "date": str(row.date),
            "count": row.count,
            "size": row.size or 0
        }
        for row in result
    ]
    
    return {"timeline": timeline, "days": days}


@router.get("/dataset/{dataset_id}")
async def get_dataset_statistics(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed statistics for a dataset."""
    # Verify ownership
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        return {"error": "Dataset not found"}
    
    # File type distribution
    type_result = await db.execute(
        select(DataFile.data_type, func.count(DataFile.id).label("count"), func.sum(DataFile.file_size).label("size"))
        .where(DataFile.dataset_id == dataset_id)
        .group_by(DataFile.data_type)
    )
    type_distribution = [
        {"type": row.data_type, "count": row.count, "size": row.size or 0}
        for row in type_result
    ]
    
    # File extension distribution
    ext_result = await db.execute(
        select(DataFile.file_type, func.count(DataFile.id).label("count"))
        .where(DataFile.dataset_id == dataset_id)
        .group_by(DataFile.file_type)
        .order_by(func.count(DataFile.id).desc())
        .limit(10)
    )
    extension_distribution = [
        {"extension": row.file_type, "count": row.count}
        for row in ext_result
    ]
    
    # Size distribution
    size_buckets = [
        ("< 100KB", 0, 100 * 1024),
        ("100KB - 1MB", 100 * 1024, 1024 * 1024),
        ("1MB - 10MB", 1024 * 1024, 10 * 1024 * 1024),
        ("10MB - 100MB", 10 * 1024 * 1024, 100 * 1024 * 1024),
        ("> 100MB", 100 * 1024 * 1024, None),
    ]
    
    size_distribution = []
    for label, min_size, max_size in size_buckets:
        if max_size:
            count_result = await db.execute(
                select(func.count(DataFile.id))
                .where(
                    DataFile.dataset_id == dataset_id,
                    DataFile.file_size >= min_size,
                    DataFile.file_size < max_size
                )
            )
        else:
            count_result = await db.execute(
                select(func.count(DataFile.id))
                .where(
                    DataFile.dataset_id == dataset_id,
                    DataFile.file_size >= min_size
                )
            )
        size_distribution.append({"range": label, "count": count_result.scalar()})
    
    # Paired data stats
    paired_result = await db.execute(
        select(func.count(DataFile.id))
        .where(
            DataFile.dataset_id == dataset_id,
            DataFile.paired_text.isnot(None)
        )
    )
    paired_count = paired_result.scalar()
    
    return {
        "dataset_id": dataset_id,
        "dataset_name": dataset.name,
        "total_files": dataset.total_files,
        "total_size": dataset.total_size,
        "type_distribution": type_distribution,
        "extension_distribution": extension_distribution,
        "size_distribution": size_distribution,
        "paired_files": paired_count,
    }
