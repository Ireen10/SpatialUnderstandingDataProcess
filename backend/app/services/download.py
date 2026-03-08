"""
Download service for datasets
"""

import asyncio
import os
import re
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

import httpx
import aiohttp
from huggingface_hub import snapshot_download, HfApi, hf_hub_download
from huggingface_hub.utils import RepositoryNotFoundError

from app.core.config import settings
from app.models.dataset import Dataset, DataFile, DataStatus, DataType
from app.models.task import Task, TaskStatus, TaskType


class DownloadService:
    """Service for downloading datasets from various sources."""
    
    def __init__(self):
        self.proxy = {}
        if settings.HTTP_PROXY:
            self.proxy["http"] = settings.HTTP_PROXY
        if settings.HTTPS_PROXY:
            self.proxy["https"] = settings.HTTPS_PROXY
        
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_dataset_path(self, dataset_name: str) -> Path:
        """Get storage path for a dataset."""
        safe_name = re.sub(r'[^\w\-_.]', '_', dataset_name)
        return self.storage_path / safe_name
    
    async def download_from_huggingface(
        self,
        repo_id: str,
        dataset: Dataset,
        task: Optional[Task] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        allow_patterns: Optional[list[str]] = None,
        ignore_patterns: Optional[list[str]] = None,
    ) -> bool:
        """
        Download a dataset from HuggingFace Hub.
        
        Args:
            repo_id: HuggingFace repo ID (e.g., "username/dataset-name")
            dataset: Dataset database record
            task: Optional task record for progress tracking
            progress_callback: Optional callback for progress updates
            allow_patterns: Optional list of patterns to include
            ignore_patterns: Optional list of patterns to exclude
        
        Returns:
            True if successful, False otherwise
        """
        try:
            dest_path = self._get_dataset_path(dataset.name)
            
            if task:
                task.status = TaskStatus.RUNNING.value
                task.started_at = datetime.utcnow()
            
            # Validate repo exists
            api = HfApi()
            try:
                api.repo_info(repo_id=repo_id, repo_type="dataset")
            except RepositoryNotFoundError:
                raise ValueError(f"HuggingFace dataset '{repo_id}' not found")
            
            # Download in thread pool to avoid blocking
            def sync_download():
                return snapshot_download(
                    repo_id=repo_id,
                    repo_type="dataset",
                    local_dir=str(dest_path),
                    local_dir_use_symlinks=False,
                    allow_patterns=allow_patterns,
                    ignore_patterns=ignore_patterns,
                    proxies=self.proxy if self.proxy else None,
                )
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, sync_download)
            
            # Scan and index downloaded files
            await self._index_downloaded_files(dest_path, dataset)
            
            if task:
                task.status = TaskStatus.COMPLETED.value
                task.progress = 100
                task.completed_at = datetime.utcnow()
            
            return True
            
        except Exception as e:
            if task:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
            raise
    
    async def download_from_url(
        self,
        url: str,
        dataset: Dataset,
        task: Optional[Task] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> bool:
        """
        Download a file from URL.
        
        Args:
            url: Direct download URL
            dataset: Dataset database record
            task: Optional task record for progress tracking
            progress_callback: Optional callback for progress updates
        
        Returns:
            True if successful, False otherwise
        """
        try:
            dest_path = self._get_dataset_path(dataset.name)
            dest_path.mkdir(parents=True, exist_ok=True)
            
            if task:
                task.status = TaskStatus.RUNNING.value
                task.started_at = datetime.utcnow()
            
            filename = url.split("/")[-1].split("?")[0]
            if not filename:
                filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            file_path = dest_path / filename
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, proxy=self.proxy.get("http") if self.proxy else None) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to download: HTTP {response.status}")
                    
                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0
                    
                    with open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size and progress_callback:
                                progress = int((downloaded / total_size) * 100)
                                progress_callback(progress)
                                if task:
                                    task.progress = progress
            
            # Index downloaded file
            await self._index_downloaded_files(dest_path, dataset)
            
            if task:
                task.status = TaskStatus.COMPLETED.value
                task.progress = 100
                task.completed_at = datetime.utcnow()
            
            return True
            
        except Exception as e:
            if task:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
            raise
    
    async def _index_downloaded_files(self, path: Path, dataset: Dataset, db_session=None) -> int:
        """
        Scan directory and create DataFile records.
        
        Returns:
            Number of files indexed
        """
        count = 0
        total_size = 0
        
        # File type mappings
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
        text_extensions = {'.txt', '.json', '.jsonl', '.csv', '.xml', '.html'}
        
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
            
            if file_path.name.startswith('.'):
                continue
            
            relative_path = file_path.relative_to(path)
            file_size = file_path.stat().st_size
            total_size += file_size
            
            # Determine file type
            ext = file_path.suffix.lower()
            if ext in image_extensions:
                data_type = DataType.IMAGE.value
                file_type = f"image/{ext[1:]}"
            elif ext in video_extensions:
                data_type = DataType.VIDEO.value
                file_type = f"video/{ext[1:]}"
            elif ext in text_extensions:
                data_type = DataType.TEXT.value
                file_type = f"text/{ext[1:]}" if ext != '.jsonl' else "application/jsonl"
            else:
                data_type = DataType.TEXT.value
                file_type = "application/octet-stream"
            
            # Check for paired text file
            paired_text = None
            if data_type in [DataType.IMAGE.value, DataType.VIDEO.value]:
                text_file = file_path.with_suffix('.txt')
                if text_file.exists():
                    paired_text = text_file.read_text(encoding='utf-8', errors='ignore')
                else:
                    json_file = file_path.with_suffix('.json')
                    if json_file.exists():
                        paired_text = json_file.read_text(encoding='utf-8', errors='ignore')
            
            # Create DataFile record (will be added to session by caller)
            data_file = DataFile(
                dataset_id=dataset.id,
                filename=file_path.name,
                relative_path=str(relative_path),
                file_size=file_size,
                file_type=file_type,
                data_type=data_type,
                status=DataStatus.READY.value,
                paired_text=paired_text,
            )
            
            if db_session:
                db_session.add(data_file)
            
            count += 1
        
        # Update dataset stats
        dataset.total_files = count
        dataset.total_size = total_size
        dataset.storage_path = str(path.relative_to(self.storage_path))
        
        return count


# Singleton instance
download_service = DownloadService()
