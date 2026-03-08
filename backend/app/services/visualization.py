"""
Visualization service for data preview
"""

import os
import base64
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from PIL import Image
import cv2

from app.core.config import settings
from app.models.dataset import DataFile, DataType


class VisualizationService:
    """Service for generating data visualizations."""
    
    def __init__(self):
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
        self.max_preview_size = 1920  # Max dimension for preview images
        self.thumbnail_size = 256
    
    def _get_file_path(self, data_file: DataFile) -> Path:
        """Get absolute path to data file."""
        return self.storage_path / data_file.relative_path
    
    def _encode_image_base64(self, image_path: Path, max_size: int = None) -> Optional[str]:
        """Encode image to base64 string with optional resize."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if needed
                if max_size and (img.width > max_size or img.height > max_size):
                    ratio = min(max_size / img.width, max_size / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Encode to base64
                import io
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            return None
    
    def _get_video_thumbnail(self, video_path: Path) -> Optional[str]:
        """Extract thumbnail from video."""
        try:
            cap = cv2.VideoCapture(str(video_path))
            if cap.isOpened():
                # Get frame from middle of video
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
                
                ret, frame = cap.read()
                cap.release()
                
                if ret:
                    # Convert BGR to RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    
                    # Resize
                    if img.width > self.thumbnail_size or img.height > self.thumbnail_size:
                        ratio = min(self.thumbnail_size / img.width, self.thumbnail_size / img.height)
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # Encode
                    import io
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=85)
                    return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error extracting video thumbnail {video_path}: {e}")
        return None
    
    async def get_preview_data(self, data_file: DataFile) -> Dict[str, Any]:
        """
        Get preview data for a file.
        
        Returns dict with preview information based on file type.
        """
        file_path = self._get_file_path(data_file)
        
        if not file_path.exists():
            return {"error": "File not found", "exists": False}
        
        result = {
            "id": data_file.id,
            "filename": data_file.filename,
            "file_type": data_file.file_type,
            "data_type": data_file.data_type,
            "file_size": data_file.file_size,
            "exists": True,
        }
        
        if data_file.data_type == DataType.IMAGE.value:
            # Image preview
            preview = self._encode_image_base64(file_path, self.max_preview_size)
            thumbnail = self._encode_image_base64(file_path, self.thumbnail_size)
            
            result.update({
                "preview_url": f"data:image/jpeg;base64,{preview}" if preview else None,
                "thumbnail_url": f"data:image/jpeg;base64,{thumbnail}" if thumbnail else None,
                "paired_text": data_file.paired_text,
            })
            
        elif data_file.data_type == DataType.VIDEO.value:
            # Video preview
            thumbnail = self._get_video_thumbnail(file_path)
            
            result.update({
                "video_url": f"/api/v1/files/{data_file.id}/raw",
                "thumbnail_url": f"data:image/jpeg;base64,{thumbnail}" if thumbnail else None,
                "paired_text": data_file.paired_text,
            })
            
        elif data_file.data_type == DataType.TEXT.value:
            # Text preview
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                # Limit preview size
                if len(content) > 10000:
                    content = content[:10000] + "\n\n... (truncated)"
                result["content"] = content
            except Exception as e:
                result["content"] = f"Error reading file: {e}"
        
        return result
    
    async def get_batch_preview(self, data_files: List[DataFile], max_items: int = 50) -> List[Dict[str, Any]]:
        """Get preview data for multiple files."""
        results = []
        for data_file in data_files[:max_items]:
            preview = await self.get_preview_data(data_file)
            results.append(preview)
        return results
    
    def generate_html_gallery(self, data_files: List[DataFile], title: str = "Data Gallery") -> str:
        """Generate HTML gallery for image/video files."""
        html_parts = [f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        h1 {{ margin-bottom: 20px; color: #333; }}
        .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; }}
        .item {{ background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .item img, .item video {{ width: 100%; height: 200px; object-fit: cover; }}
        .item .info {{ padding: 12px; }}
        .item .filename {{ font-size: 14px; font-weight: 500; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .item .meta {{ font-size: 12px; color: #666; margin-top: 4px; }}
        .item .text {{ padding: 12px; font-size: 13px; color: #444; max-height: 100px; overflow-y: auto; background: #f9f9f9; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="gallery">
"""]
        
        for df in data_files:
            file_path = self._get_file_path(df)
            
            if df.data_type == DataType.IMAGE.value:
                thumbnail = self._encode_image_base64(file_path, self.thumbnail_size)
                if thumbnail:
                    text_html = f'<div class="text">{df.paired_text[:200]}</div>' if df.paired_text else ''
                    html_parts.append(f'''
        <div class="item">
            <img src="data:image/jpeg;base64,{thumbnail}" alt="{df.filename}">
            <div class="info">
                <div class="filename" title="{df.filename}">{df.filename}</div>
                <div class="meta">{df.file_type} • {df.file_size // 1024}KB</div>
            </div>
            {text_html}
        </div>
''')
            elif df.data_type == DataType.VIDEO.value:
                thumbnail = self._get_video_thumbnail(file_path)
                if thumbnail:
                    text_html = f'<div class="text">{df.paired_text[:200]}</div>' if df.paired_text else ''
                    html_parts.append(f'''
        <div class="item">
            <img src="data:image/jpeg;base64,{thumbnail}" alt="{df.filename}">
            <div class="info">
                <div class="filename" title="{df.filename}">{df.filename}</div>
                <div class="meta">Video • {df.file_size // (1024*1024)}MB</div>
            </div>
            {text_html}
        </div>
''')
        
        html_parts.append("""
    </div>
</body>
</html>
""")
        
        return "".join(html_parts)


# Singleton
visualization_service = VisualizationService()
