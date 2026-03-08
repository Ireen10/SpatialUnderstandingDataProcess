"""
Authentication and authorization dependencies
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, APIKey, UserRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require admin role."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_user_by_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate user by API key (for external API calls)."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required"
        )
    
    # Find API key by hash (simplified - use proper hashing in production)
    result = await db.execute(
        select(APIKey).options(selectinload(APIKey.user)).where(
            APIKey.is_active == True
        )
    )
    api_keys = result.scalars().all()
    
    # Verify key (simplified)
    for ak in api_keys:
        if x_api_key.startswith(ak.key_prefix):
            # Check quota
            if ak.quota_used >= ak.quota_limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="API quota exceeded"
                )
            return ak.user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key"
    )
