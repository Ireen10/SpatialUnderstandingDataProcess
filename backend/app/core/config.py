"""
Core configuration and settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Project
    PROJECT_NAME: str = "SpatialUnderstandingDataProcess"
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./spatial_v2.db",
        description="Database URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for Celery"
    )
    
    # Storage
    DATA_STORAGE_PATH: str = Field(
        default="../data",
        description="Path to store data files (relative to backend/)"
    )
    STORAGE_BACKEND: str = Field(
        default="local",
        description="Storage backend: local or s3"
    )
    
    # S3 (optional)
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    
    # Proxy
    HTTP_PROXY: Optional[str] = None
    HTTPS_PROXY: Optional[str] = None
    
    # LLM (OpenRouter)
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "z-ai/glm-5"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
