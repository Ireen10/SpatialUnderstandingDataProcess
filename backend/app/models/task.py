"""
Task model for async job tracking
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    DOWNLOAD = "download"
    CONVERT = "convert"
    EXPORT = "export"
    BACKUP = "backup"
    METADATA_EXTRACT = "metadata_extract"
    VISUALIZATION = "visualization"
    CUSTOM = "custom"


class Task(Base, TimestampMixin):
    """Async task tracking."""
    
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    # Task identification
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    task_type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.PENDING.value, nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100
    
    # Input/Output
    input_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    output_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Related resources
    dataset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    data_file_id: Mapped[Optional[int]] = mapped_column(ForeignKey("data_files.id"), nullable=True)
    
    # Retry info
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="tasks")
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, type='{self.task_type}', status='{self.status}', progress={self.progress}%)>"
