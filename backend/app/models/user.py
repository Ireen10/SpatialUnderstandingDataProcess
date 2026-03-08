"""
User and API Key models
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin
import secrets
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base, TimestampMixin):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.USER.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    api_keys: Mapped[List["APIKey"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    datasets: Mapped[List["Dataset"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class APIKey(Base, TimestampMixin):
    """API Key for user authentication and quota management."""
    
    __tablename__ = "api_keys"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)  # For display purposes
    
    # LLM Configuration (user can override system defaults)
    llm_api_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    llm_api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Encrypted
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Quota management
    quota_limit: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)  # Max requests
    quota_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quota_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="api_keys")
    
    @staticmethod
    def generate_key() -> tuple[str, str]:
        """Generate a new API key. Returns (plain_key, key_hash)."""
        plain_key = f"sk_{secrets.token_urlsafe(32)}"
        # In production, use proper hashing like bcrypt
        key_hash = secrets.token_urlsafe(32)  # Placeholder - use bcrypt in production
        return plain_key, key_hash
    
    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"
