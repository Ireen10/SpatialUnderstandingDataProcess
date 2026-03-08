"""
Dataset, DataFile, and Metadata models
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, JSON, BigInteger, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin
from enum import Enum


class DataStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class DataType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    IMAGE_TEXT = "image_text"
    VIDEO_TEXT = "video_text"


class Dataset(Base, TimestampMixin):
    """Dataset collection - user's data container."""
    
    __tablename__ = "datasets"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Storage info
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)  # Relative path
    storage_backend: Mapped[str] = mapped_column(String(20), default="local", nullable=False)
    
    # Statistics
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # Bytes
    
    # Version info
    version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)
    
    # Relationships
    owner: Mapped["User"] = relationship(back_populates="datasets")
    files: Mapped[List["DataFile"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name='{self.name}', files={self.total_files})>"


class DataFile(Base, TimestampMixin):
    """Individual data file within a dataset."""
    
    __tablename__ = "data_files"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False, index=True)
    
    # File info
    filename: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Bytes
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # mime type
    data_type: Mapped[str] = mapped_column(String(20), default=DataType.IMAGE.value, nullable=False)
    
    # Checksum for integrity
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default=DataStatus.READY.value, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Paired data (for image-text, video-text pairs)
    paired_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    paired_text_file: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Custom metadata (JSON)
    custom_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    dataset: Mapped["Dataset"] = relationship(back_populates="files")
    file_metadata: Mapped[Optional["FileMetadata"]] = relationship(back_populates="data_file", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<DataFile(id={self.id}, filename='{self.filename}', type='{self.data_type}')>"


class FileMetadata(Base, TimestampMixin):
    """Extended metadata for data files."""
    
    __tablename__ = "file_metadata"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data_file_id: Mapped[int] = mapped_column(ForeignKey("data_files.id"), unique=True, nullable=False)
    
    # Image metadata
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    channels: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bit_depth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Video metadata
    duration: Mapped[Optional[float]] = mapped_column(nullable=True)  # Seconds
    fps: Mapped[Optional[float]] = mapped_column(nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Text metadata
    text_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # EXIF / raw metadata
    exif_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    raw_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    data_file: Mapped["DataFile"] = relationship(back_populates="file_metadata")
    
    def __repr__(self) -> str:
        return f"<FileMetadata(id={self.id}, data_file_id={self.data_file_id})>"
