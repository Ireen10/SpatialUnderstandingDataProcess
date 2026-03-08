"""
Search endpoints for data
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset, DataFile
from app.schemas import DataFileResponse, PaginatedResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/files", response_model=PaginatedResponse)
async def search_files(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    data_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search files by name."""
    # Build query
    query = (
        select(DataFile)
        .join(Dataset)
        .where(Dataset.user_id == current_user.id)
        .where(
            or_(
                DataFile.filename.ilike(f"%{q}%"),
                DataFile.relative_path.ilike(f"%{q}%"),
            )
        )
    )
    
    if data_type:
        query = query.where(DataFile.data_type == data_type)
    
    # Count total
    count_query = (
        select(func.count(DataFile.id))
        .join(Dataset)
        .where(Dataset.user_id == current_user.id)
        .where(
            or_(
                DataFile.filename.ilike(f"%{q}%"),
                DataFile.relative_path.ilike(f"%{q}%"),
            )
        )
    )
    if data_type:
        count_query = count_query.where(DataFile.data_type == data_type)
    
    total = (await db.execute(count_query)).scalar()
    
    # Get results
    query = query.order_by(DataFile.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    files = result.scalars().all()
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[DataFileResponse.model_validate(f) for f in files],
    )


@router.get("/datasets")
async def search_datasets(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search datasets by name."""
    result = await db.execute(
        select(Dataset)
        .where(Dataset.user_id == current_user.id)
        .where(Dataset.name.ilike(f"%{q}%"))
        .order_by(Dataset.created_at.desc())
    )
    datasets = result.scalars().all()
    
    return {"results": [{"id": d.id, "name": d.name, "total_files": d.total_files} for d in datasets]}
