"""
Initialization and configuration endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.services.init import init_service

router = APIRouter(prefix="/init", tags=["initialization"])


class InitRequest(BaseModel):
    """Initialization request."""
    # Required
    data_path: str
    admin_username: str = "admin"
    admin_email: EmailStr
    admin_password: str
    
    # Optional - API
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_model: Optional[str] = None
    
    # Optional - Proxy
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    
    # Optional - Storage
    storage_backend: str = "local"  # local, s3, minio
    s3_endpoint: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_bucket: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    """Config update request."""
    # API
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_model: Optional[str] = None
    
    # Proxy
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    
    # Storage
    storage_backend: Optional[str] = None
    s3_endpoint: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_bucket: Optional[str] = None


@router.get("/status")
async def get_init_status():
    """
    Get initialization status.
    
    Returns whether the system has been initialized and what's missing.
    This is a public endpoint - no authentication required.
    """
    return init_service.get_init_status()


@router.post("/initialize")
async def initialize_system(
    request: InitRequest,
):
    """
    Initialize the system for first use.
    
    This is a public endpoint that can only be called once.
    Creates the admin account and sets up basic configuration.
    """
    # Check if already initialized
    if init_service.is_initialized():
        raise HTTPException(
            status_code=400,
            detail="System already initialized. Use /init/config to update settings."
        )
    
    # Validate required fields
    if not request.data_path:
        raise HTTPException(status_code=400, detail="Data path is required")
    
    if not request.admin_email:
        raise HTTPException(status_code=400, detail="Admin email is required")
    
    if not request.admin_password or len(request.admin_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    try:
        result = init_service.initialize(
            data_path=request.data_path,
            admin_username=request.admin_username,
            admin_email=request.admin_email,
            admin_password=request.admin_password,
            api_base_url=request.api_base_url,
            api_key=request.api_key,
            api_model=request.api_model,
            http_proxy=request.http_proxy,
            https_proxy=request.https_proxy,
            storage_backend=request.storage_backend,
            s3_endpoint=request.s3_endpoint,
            s3_access_key=request.s3_access_key,
            s3_secret_key=request.s3_secret_key,
            s3_bucket=request.s3_bucket,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config")
async def get_config():
    """Get current configuration (public for init wizard)."""
    if not init_service.is_initialized():
        return {"initialized": False, "config": {}}
    
    return {
        "initialized": True,
        "config": init_service.get_config(),
    }


@router.put("/config")
async def update_config(
    request: ConfigUpdateRequest,
):
    """
    Update system configuration.
    
    In production, this should require admin authentication.
    For initial setup, it's public.
    """
    updates = request.model_dump(exclude_none=True)
    
    result = init_service.update_config(updates)
    return result