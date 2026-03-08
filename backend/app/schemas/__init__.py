"""
Pydantic schemas for API request/response
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole
from app.models.dataset import DataStatus, DataType
from app.models.task import TaskStatus, TaskType


# ==================== User Schemas ====================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int  # user_id
    exp: datetime


# ==================== API Key Schemas ====================

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    llm_api_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    quota_limit: int = Field(default=1000, ge=0)


class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    llm_model: Optional[str]
    quota_limit: int
    quota_used: int
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class APIKeyCreated(APIKeyResponse):
    key: str  # Only shown once on creation


# ==================== Dataset Schemas ====================

class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    storage_path: str = Field(default="datasets")


class DatasetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    storage_path: str
    total_files: int
    total_size: int
    version: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== DataFile Schemas ====================

class DataFileResponse(BaseModel):
    id: int
    filename: str
    relative_path: str
    file_size: int
    file_type: str
    data_type: str
    status: str
    paired_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DataFileWithMetadata(DataFileResponse):
    custom_metadata: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


# ==================== Task Schemas ====================

class TaskCreate(BaseModel):
    task_type: TaskType
    name: str
    input_params: Optional[Dict[str, Any]] = None
    dataset_id: Optional[int] = None
    data_file_id: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    task_type: str
    name: str
    status: str
    progress: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TaskWithResult(TaskResponse):
    output_result: Optional[Dict[str, Any]] = None


# ==================== Common Schemas ====================

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
