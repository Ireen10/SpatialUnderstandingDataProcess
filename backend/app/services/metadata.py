"""
Metadata extraction service
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from PIL import Image
import cv2
import numpy as np

from app.models.dataset import DataFile, FileMetadata, DataType


class MetadataService:
    """Service for extracting metadata from various file types."""
    
    @staticmethod
    async def extract_metadata(data_file: DataFile, file_path: Path) -> Optional[FileMetadata]:
        """
        Extract metadata from a data file.
        
        Args:
            data_file: DataFile record
            file_path: Path to the actual file
        
        Returns:
            Metadata record or None
        """
        try:
            if data_file.data_type == DataType.IMAGE.value:
                return await MetadataService._extract_image_metadata(data_file, file_path)
            elif data_file.data_type == DataType.VIDEO.value:
                return await MetadataService._extract_video_metadata(data_file, file_path)
            elif data_file.data_type == DataType.TEXT.value:
                return await MetadataService._extract_text_metadata(data_file, file_path)
        except Exception as e:
            # Log error but don't fail
            print(f"Failed to extract metadata for {file_path}: {e}")
            return None
        
        return None
    
    @staticmethod
    async def _extract_image_metadata(data_file: DataFile, file_path: Path) -> FileMetadata:
        """Extract metadata from image file."""
        metadata = FileMetadata(data_file_id=data_file.id)
        
        try:
            with Image.open(file_path) as img:
                metadata.width = img.width
                metadata.height = img.height
                metadata.channels = len(img.getbands()) if img.getbands() else None
                metadata.bit_depth = 8 if img.mode in ('L', 'RGB', 'RGBA') else None
                
                # Extract EXIF data
                if hasattr(img, '_getexif') and img._getexif():
                    exif = {}
                    for tag_id, value in img._getexif().items():
                        try:
                            # Convert to JSON-serializable
                            if isinstance(value, bytes):
                                value = value.hex()
                            elif isinstance(value, tuple):
                                value = list(value)
                            exif[str(tag_id)] = value
                        except:
                            pass
                    metadata.exif_data = exif
        except Exception as e:
            print(f"Error reading image metadata: {e}")
        
        return metadata
    
    @staticmethod
    async def _extract_video_metadata(data_file: DataFile, file_path: Path) -> FileMetadata:
        """Extract metadata from video file."""
        metadata = FileMetadata(data_file_id=data_file.id)
        
        try:
            cap = cv2.VideoCapture(str(file_path))
            
            if cap.isOpened():
                metadata.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                metadata.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                metadata.fps = cap.get(cv2.CAP_PROP_FPS)
                metadata.duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / metadata.fps if metadata.fps else None
                metadata.codec = int(cap.get(cv2.CAP_PROP_FOURCC)).to_bytes(4, 'little').decode('utf-8', errors='ignore')
                
                # Get frame count
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                metadata.raw_metadata = {
                    "frame_count": frame_count,
                    "fourcc": metadata.codec,
                }
                
            cap.release()
        except Exception as e:
            print(f"Error reading video metadata: {e}")
        
        return metadata
    
    @staticmethod
    async def _extract_text_metadata(data_file: DataFile, file_path: Path) -> FileMetadata:
        """Extract metadata from text file."""
        metadata = FileMetadata(data_file_id=data_file.id)
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            metadata.text_length = len(content)
            metadata.word_count = len(content.split())
            
            # Try to detect language (simple heuristic)
            # Could integrate langdetect for better detection
            metadata.language = None
            
            # If JSON, extract structure info
            if file_path.suffix.lower() in ('.json', '.jsonl'):
                try:
                    if file_path.suffix.lower() == '.jsonl':
                        # JSONL: count lines and sample first record
                        lines = content.strip().split('\n')
                        metadata.raw_metadata = {
                            "record_count": len(lines),
                            "format": "jsonl",
                        }
                    else:
                        data = json.loads(content)
                        metadata.raw_metadata = {
                            "type": type(data).__name__,
                            "keys": list(data.keys()) if isinstance(data, dict) else None,
                            "length": len(data) if isinstance(data, (list, dict)) else None,
                        }
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"Error reading text metadata: {e}")
        
        return metadata


# Singleton instance
metadata_service = MetadataService()
