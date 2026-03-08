"""
Conversion and export endpoints
"""

from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset, DataFile
from app.models.task import Task, TaskStatus, TaskType
from app.schemas import TaskResponse, MessageResponse
from app.services.conversion import conversion_service
from app.services.schema_mapping import schema_mapping_service
import fnmatch

router = APIRouter(prefix="/tools", tags=["tools"])


# ==================== Conversion ====================

class ConversionRequest(BaseModel):
    target_format: str
    output_path: Optional[str] = None
    options: Optional[dict] = None


class AnnotationConversionRequest(BaseModel):
    source_format: str  # coco, yolo, voc
    target_format: str
    classes: Optional[List[str]] = None


@router.post("/datasets/{dataset_id}/convert", response_model=TaskResponse)
async def convert_dataset(
    dataset_id: int,
    request: ConversionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert dataset to target format."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    task = Task(
        user_id=current_user.id,
        task_type=TaskType.CONVERT.value,
        name=f"Convert to {request.target_format}",
        input_params={
            "target_format": request.target_format,
            "output_path": request.output_path,
            "options": request.options,
        },
        dataset_id=dataset_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # Run conversion
    output_path = Path(request.output_path) if request.output_path else None
    
    try:
        await conversion_service.convert_dataset(
            dataset=dataset,
            target_format=request.target_format,
            output_path=output_path,
            task=task,
            options=request.options,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    await db.refresh(task)
    return task


@router.post("/datasets/{dataset_id}/convert-annotations", response_model=TaskResponse)
async def convert_annotations(
    dataset_id: int,
    request: AnnotationConversionRequest,
    annotations_file: str = Query(..., description="Path to annotations file relative to dataset"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert annotation format (COCO, YOLO, VOC)."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    source_path = Path(settings.DATA_STORAGE_PATH) / dataset.storage_path / annotations_file
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Annotations file not found")
    
    task = Task(
        user_id=current_user.id,
        task_type=TaskType.CONVERT.value,
        name=f"Convert {request.source_format} -> {request.target_format}",
        input_params={
            "source_format": request.source_format,
            "target_format": request.target_format,
            "annotations_file": annotations_file,
        },
        dataset_id=dataset_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    output_dir = Path(settings.DATA_STORAGE_PATH) / dataset.storage_path / "converted"
    
    try:
        task.status = TaskStatus.RUNNING.value
        await conversion_service.convert_annotations(
            source_format=request.source_format,
            target_format=request.target_format,
            annotations_file=source_path,
            output_dir=output_dir,
            classes=request.classes,
        )
        task.status = TaskStatus.COMPLETED.value
        task.progress = 100
        await db.commit()
    except Exception as e:
        task.status = TaskStatus.FAILED.value
        task.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    
    await db.refresh(task)
    return task


# ==================== Schema Mapping ====================

class SchemaMappingRequest(BaseModel):
    """Request for JSON schema transformation."""
    mapping: dict
    output_filename: Optional[str] = None
    options: Optional[dict] = None


class InferMappingRequest(BaseModel):
    """Request to infer mapping from samples."""
    source_sample: dict
    target_sample: dict


@router.post("/files/{file_id}/transform-schema")
async def transform_file_schema(
    file_id: int,
    request: SchemaMappingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Transform a JSON/JSONL file based on field mapping.
    
    Mapping format:
    ```json
    {
        "field_mappings": {
            "old_field": "new_field",
            "image_path": "image",
            "caption": "text"
        },
        "value_transforms": {
            "status": {
                "type": "rename_values",
                "mappings": {"old": "new"}
            },
            "name": {"type": "case", "case": "lower"}
        },
        "field_operations": {
            "full_name": {
                "type": "concat",
                "sources": ["first_name", "last_name"],
                "separator": " "
            }
        },
        "exclude_fields": ["internal_id"],
        "add_fields": {"version": "1.0"}
    }
    ```
    """
    result = await db.execute(
        select(DataFile)
        .options(selectinload(DataFile.dataset))
        .where(DataFile.id == file_id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.dataset.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Only JSON/JSONL files
    if not file.filename.lower().endswith(('.json', '.jsonl')):
        raise HTTPException(status_code=400, detail="Only JSON/JSONL files are supported")
    
    input_path = Path(settings.DATA_STORAGE_PATH) / file.relative_path
    
    # Determine output path
    output_filename = request.output_filename or f"{file.stem}_transformed{file.suffix}"
    output_path = Path(settings.DATA_STORAGE_PATH) / file.dataset.storage_path / output_filename
    
    try:
        stats = await schema_mapping_service.transform_file(
            input_path=input_path,
            output_path=output_path,
            mapping=request.mapping,
            options=request.options,
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/infer-mapping")
async def infer_mapping(
    request: InferMappingRequest,
    current_user: User = Depends(get_current_user),
):
    """Infer field mapping from source and target samples."""
    mapping = schema_mapping_service.infer_mapping_from_samples(
        source_sample=request.source_sample,
        target_sample=request.target_sample,
    )
    return mapping


@router.post("/validate-mapping")
async def validate_mapping(
    mapping: dict,
    current_user: User = Depends(get_current_user),
):
    """Validate a schema mapping configuration."""
    result = schema_mapping_service.validate_mapping(mapping)
    return result


@router.post("/datasets/{dataset_id}/transform-all")
async def transform_dataset_files(
    dataset_id: int,
    request: SchemaMappingRequest,
    file_pattern: str = Query("*.json", description="Glob pattern for files to transform"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transform all matching files in a dataset based on schema mapping."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    result = await db.execute(
        select(DataFile).where(
            DataFile.dataset_id == dataset_id,
            DataFile.filename.ilike(f"%{file_pattern.replace('*', '')}%")
        )
    )
    files = result.scalars().all()
    
    # Filter by actual pattern
    import fnmatch
    files = [f for f in files if fnmatch.fnmatch(f.filename.lower(), file_pattern.lower())]
    
    if not files:
        raise HTTPException(status_code=404, detail="No matching files found")
    
    output_dir = Path(settings.DATA_STORAGE_PATH) / dataset.storage_path / "transformed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    for file in files:
        if not file.filename.lower().endswith(('.json', '.jsonl')):
            continue
        
        input_path = Path(settings.DATA_STORAGE_PATH) / file.relative_path
        output_path = output_dir / f"{file.stem}_transformed{file.suffix}"
        
        try:
            stats = await schema_mapping_service.transform_file(
                input_path=input_path,
                output_path=output_path,
                mapping=request.mapping,
                options=request.options,
            )
            results.append(stats)
        except Exception as e:
            results.append({
                "file": file.filename,
                "error": str(e),
            })
    
    return {
        "total_files": len(files),
        "transformed": len([r for r in results if "error" not in r]),
        "failed": len([r for r in results if "error" in r]),
        "results": results,
    }


# ==================== Export ====================

class ExportRequest(BaseModel):
    format: str = "zip"  # zip, tar, raw
    include_metadata: bool = True
    filters: Optional[dict] = None


class TrainingExportRequest(BaseModel):
    output_format: str = "jsonl"


@router.post("/datasets/{dataset_id}/export", response_model=TaskResponse)
async def export_dataset(
    dataset_id: int,
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export dataset as downloadable archive."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Get files
    result = await db.execute(
        select(DataFile).where(DataFile.dataset_id == dataset_id)
    )
    files = result.scalars().all()
    
    task = Task(
        user_id=current_user.id,
        task_type=TaskType.EXPORT.value,
        name=f"Export as {request.format}",
        input_params={
            "format": request.format,
            "include_metadata": request.include_metadata,
            "filters": request.filters,
        },
        dataset_id=dataset_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    try:
        await export_service.export_dataset(
            dataset=dataset,
            files=files,
            output_format=request.format,
            task=task,
            include_metadata=request.include_metadata,
            filters=request.filters,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    await db.refresh(task)
    return task


@router.post("/datasets/{dataset_id}/export-training", response_model=TaskResponse)
async def export_for_training(
    dataset_id: int,
    request: TrainingExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export dataset in VLM training format (image-text pairs)."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    result = await db.execute(
        select(DataFile)
        .options(selectinload(DataFile.file_metadata))
        .where(DataFile.dataset_id == dataset_id, DataFile.paired_text.isnot(None))
    )
    files = result.scalars().all()
    
    if not files:
        raise HTTPException(status_code=400, detail="No paired data found for training export")
    
    task = Task(
        user_id=current_user.id,
        task_type=TaskType.EXPORT.value,
        name="Export for training",
        input_params={"output_format": request.output_format},
        dataset_id=dataset_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    try:
        await export_service.export_for_training(
            dataset=dataset,
            files=files,
            output_format=request.output_format,
            task=task,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    await db.refresh(task)
    return task


@router.get("/exports")
async def list_exports(
    current_user: User = Depends(get_current_user),
):
    """List all exports."""
    exports = export_service.list_exports()
    return {"exports": exports}


@router.delete("/exports/{export_name}")
async def delete_export(
    export_name: str,
    current_user: User = Depends(get_current_user),
):
    """Delete an export."""
    if export_service.delete_export(export_name):
        return {"message": "Export deleted"}
    raise HTTPException(status_code=404, detail="Export not found")
