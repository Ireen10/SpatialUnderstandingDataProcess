"""
Data version management endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.services.version import version_service

router = APIRouter(prefix="/versions", tags=["versions"])


class CreateVersionRequest(BaseModel):
    version_name: str
    description: Optional[str] = None


class CompareRequest(BaseModel):
    version_id_1: str
    version_id_2: str


@router.get("/info")
async def get_version_info(
    current_user: User = Depends(get_current_user),
):
    """Get versioning system info."""
    return version_service.get_version_info()


@router.post("/datasets/{dataset_id}")
async def create_version(
    dataset_id: int,
    request: CreateVersionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new version of a dataset."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        version = await version_service.create_version(
            dataset=dataset,
            version_name=request.version_name,
            description=request.description,
            author=current_user.username,
        )
        return version
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_versions(
    dataset_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """List all versions."""
    versions = version_service.list_versions(dataset_id)
    return {"versions": versions}


@router.get("/{version_id}")
async def get_version(
    version_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get version details."""
    version = version_service.get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.post("/{version_id}/restore")
async def restore_version(
    version_id: str,
    dataset_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore dataset to a specific version."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        result = await version_service.restore_version(version_id, dataset)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{version_id}")
async def delete_version(
    version_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a version snapshot."""
    if version_service.delete_version(version_id):
        return {"message": "Version deleted"}
    raise HTTPException(status_code=404, detail="Version not found")


@router.post("/compare")
async def compare_versions(
    request: CompareRequest,
    current_user: User = Depends(get_current_user),
):
    """Compare two versions."""
    try:
        diff = version_service.compare_versions(
            request.version_id_1,
            request.version_id_2,
        )
        return diff
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
