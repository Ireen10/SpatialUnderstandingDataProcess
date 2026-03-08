"""
AI-powered features endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.models.user import User, APIKey
from app.models.dataset import Dataset, DataFile, DataType
from app.services.ai import AIService, get_ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


class VisualizationRequest(BaseModel):
    data_type: str
    sample_data: dict
    description: Optional[str] = None


class ConversionRequest(BaseModel):
    source_format: str
    target_format: str
    sample_data: Optional[dict] = None
    description: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None


@router.post("/generate-visualization")
async def generate_visualization(
    request: VisualizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate HTML visualization code using AI."""
    # Get user's API key configuration
    result = await db.execute(
        select(APIKey).where(
            APIKey.user_id == current_user.id,
            APIKey.is_active == True
        ).order_by(APIKey.created_at.desc())
    )
    api_key_record = result.scalar_one_or_none()
    
    # Use user's API key if configured, otherwise use system default
    if api_key_record and api_key_record.llm_api_key:
        service = get_ai_service(
            api_key=api_key_record.llm_api_key,
            base_url=api_key_record.llm_api_url,
            model=api_key_record.llm_model,
        )
    else:
        service = get_ai_service()
    
    if not service.api_key:
        raise HTTPException(
            status_code=400,
            detail="No API key configured. Please create an API key with your LLM credentials."
        )
    
    try:
        code = await service.generate_visualization_code(
            data_type=request.data_type,
            sample_data=request.sample_data,
            description=request.description,
        )
        
        # Update quota
        if api_key_record:
            api_key_record.quota_used += 1
        
        return {"code": code, "data_type": request.data_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-conversion-script")
async def generate_conversion_script(
    request: ConversionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate Python conversion script using AI."""
    # Get user's API key configuration
    result = await db.execute(
        select(APIKey).where(
            APIKey.user_id == current_user.id,
            APIKey.is_active == True
        ).order_by(APIKey.created_at.desc())
    )
    api_key_record = result.scalar_one_or_none()
    
    if api_key_record and api_key_record.llm_api_key:
        service = get_ai_service(
            api_key=api_key_record.llm_api_key,
            base_url=api_key_record.llm_api_url,
            model=api_key_record.llm_model,
        )
    else:
        service = get_ai_service()
    
    if not service.api_key:
        raise HTTPException(
            status_code=400,
            detail="No API key configured."
        )
    
    try:
        script = await service.generate_conversion_script(
            source_format=request.source_format,
            target_format=request.target_format,
            sample_data=request.sample_data,
            description=request.description,
        )
        
        if api_key_record:
            api_key_record.quota_used += 1
        
        return {"script": script}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-quality/{dataset_id}")
async def analyze_dataset_quality(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze dataset quality using AI."""
    # Verify ownership
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Get files with metadata
    result = await db.execute(
        select(DataFile)
        .options(selectinload(DataFile.file_metadata))
        .where(DataFile.dataset_id == dataset_id)
        .limit(100)
    )
    files = result.scalars().all()
    
    # Prepare data info
    data_info = {
        "dataset_name": dataset.name,
        "total_files": dataset.total_files,
        "total_size": dataset.total_size,
        "file_types": {},
        "data_types": {},
        "sample_files": [],
    }
    
    for f in files:
        data_info["file_types"][f.file_type] = data_info["file_types"].get(f.file_type, 0) + 1
        data_info["data_types"][f.data_type] = data_info["data_types"].get(f.data_type, 0) + 1
        
        if len(data_info["sample_files"]) < 10:
            file_info = {
                "filename": f.filename,
                "size": f.file_size,
                "type": f.data_type,
                "status": f.status,
            }
            if f.file_metadata:
                file_info["metadata"] = {
                    "width": f.file_metadata.width,
                    "height": f.file_metadata.height,
                    "duration": f.file_metadata.duration,
                }
            data_info["sample_files"].append(file_info)
    
    # Get API key
    result = await db.execute(
        select(APIKey).where(
            APIKey.user_id == current_user.id,
            APIKey.is_active == True
        ).order_by(APIKey.created_at.desc())
    )
    api_key_record = result.scalar_one_or_none()
    
    if api_key_record and api_key_record.llm_api_key:
        service = get_ai_service(
            api_key=api_key_record.llm_api_key,
            base_url=api_key_record.llm_api_url,
            model=api_key_record.llm_model,
        )
    else:
        service = get_ai_service()
    
    if not service.api_key:
        raise HTTPException(status_code=400, detail="No API key configured.")
    
    try:
        analysis = await service.analyze_data_quality(data_info)
        
        if api_key_record:
            api_key_record.quota_used += 1
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """General chat with AI assistant."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.user_id == current_user.id,
            APIKey.is_active == True
        ).order_by(APIKey.created_at.desc())
    )
    api_key_record = result.scalar_one_or_none()
    
    if api_key_record and api_key_record.llm_api_key:
        service = get_ai_service(
            api_key=api_key_record.llm_api_key,
            base_url=api_key_record.llm_api_url,
            model=api_key_record.llm_model,
        )
    else:
        service = get_ai_service()
    
    if not service.api_key:
        raise HTTPException(status_code=400, detail="No API key configured.")
    
    try:
        response = await service.chat(
            message=request.message,
            context=request.context,
            system_prompt="You are a helpful AI assistant for a data processing platform. Help users with data analysis, format conversion, and visualization questions.",
        )
        
        if api_key_record:
            api_key_record.quota_used += 1
        
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
