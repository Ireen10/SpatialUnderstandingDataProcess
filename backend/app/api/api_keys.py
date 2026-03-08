"""
API Key management endpoints
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, APIKey
from app.schemas import APIKeyCreate, APIKeyResponse, APIKeyCreated

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key."""
    plain_key, key_hash = APIKey.generate_key()
    
    api_key = APIKey(
        user_id=current_user.id,
        name=key_data.name,
        key_hash=key_hash,
        key_prefix=plain_key[:8],
        llm_api_url=key_data.llm_api_url,
        llm_api_key=key_data.llm_api_key,  # TODO: encrypt in production
        llm_model=key_data.llm_model,
        quota_limit=key_data.quota_limit,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        key=plain_key,  # Only shown once
        llm_model=api_key.llm_model,
        quota_limit=api_key.quota_limit,
        quota_used=api_key.quota_used,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
    )


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's API keys."""
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_user.id).order_by(APIKey.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific API key."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    return api_key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an API key."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    
    await db.delete(api_key)
    await db.commit()


@router.post("/{key_id}/deactivate", response_model=APIKeyResponse)
async def deactivate_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate an API key."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    
    api_key.is_active = False
    await db.commit()
    await db.refresh(api_key)
    return api_key


@router.post("/{key_id}/reset-quota", response_model=APIKeyResponse)
async def reset_quota(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset API key quota."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    
    api_key.quota_used = 0
    api_key.quota_reset_at = datetime.utcnow()
    await db.commit()
    await db.refresh(api_key)
    return api_key
