"""
File serving and visualization endpoints
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import json

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset, DataFile, DataType
from app.services.visualization import visualization_service
from app.services.metadata import metadata_service

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{file_id}/raw")
async def get_raw_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Serve raw file content."""
    result = await db.execute(
        select(DataFile)
        .options(selectinload(DataFile.dataset))
        .where(DataFile.id == file_id)
    )
    data_file = result.scalar_one_or_none()
    
    if not data_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check ownership
    if data_file.dataset.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_path = Path(settings.DATA_STORAGE_PATH) / data_file.relative_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        media_type=data_file.file_type,
        filename=data_file.filename,
    )


@router.get("/{file_id}/preview")
async def get_file_preview(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get file preview data (base64 for images, metadata for videos)."""
    result = await db.execute(
        select(DataFile)
        .options(selectinload(DataFile.dataset), selectinload(DataFile.metadata))
        .where(DataFile.id == file_id)
    )
    data_file = result.scalar_one_or_none()
    
    if not data_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if data_file.dataset.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    preview = await visualization_service.get_preview_data(data_file)
    
    # Add metadata if available
    if data_file.metadata:
        preview["metadata"] = {
            "width": data_file.metadata.width,
            "height": data_file.metadata.height,
            "duration": data_file.metadata.duration,
            "fps": data_file.metadata.fps,
            "text_length": data_file.metadata.text_length,
            "word_count": data_file.metadata.word_count,
        }
    
    return preview


@router.get("/dataset/{dataset_id}/gallery", response_class=HTMLResponse)
async def get_dataset_gallery(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate HTML gallery for dataset."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    result = await db.execute(
        select(DataFile)
        .where(DataFile.dataset_id == dataset_id)
        .limit(100)
    )
    files = result.scalars().all()
    
    html = visualization_service.generate_html_gallery(files, title=dataset.name)
    return HTMLResponse(content=html)


@router.post("/{file_id}/extract-metadata")
async def extract_file_metadata(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually extract metadata for a file."""
    result = await db.execute(
        select(DataFile)
        .options(selectinload(DataFile.dataset))
        .where(DataFile.id == file_id)
    )
    data_file = result.scalar_one_or_none()
    
    if not data_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if data_file.dataset.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_path = Path(settings.DATA_STORAGE_PATH) / data_file.relative_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    metadata = await metadata_service.extract_metadata(data_file, file_path)
    
    if metadata:
        db.add(metadata)
        await db.commit()
        await db.refresh(metadata)
        return {"message": "Metadata extracted", "metadata_id": metadata.id}
    else:
        return {"message": "No metadata could be extracted"}
