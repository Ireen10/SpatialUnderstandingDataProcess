"""
Export service for dataset export
"""

import os
import json
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

from app.core.config import settings
from app.models.dataset import Dataset, DataFile, DataType
from app.models.task import Task, TaskStatus


class ExportService:
    """Service for exporting datasets."""
    
    def __init__(self):
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
        self.exports_path = self.storage_path / "exports"
        self.exports_path.mkdir(parents=True, exist_ok=True)
    
    async def export_dataset(
        self,
        dataset: Dataset,
        files: List[DataFile],
        output_format: str = "zip",
        task: Optional[Task] = None,
        include_metadata: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Export dataset to specified format.
        
        Args:
            dataset: Dataset to export
            files: List of files to include
            output_format: Output format (zip, tar, raw)
            task: Optional task for progress tracking
            include_metadata: Include metadata JSON
            filters: Optional filters for file selection
        
        Returns:
            Path to exported file/directory
        """
        if task:
            task.status = TaskStatus.RUNNING.value
            task.started_at = datetime.utcnow()
            task.progress = 0
        
        try:
            # Create export directory
            export_name = f"{dataset.name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            export_dir = self.exports_path / export_name
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Apply filters
            filtered_files = self._apply_filters(files, filters)
            total_files = len(filtered_files)
            
            if task:
                task.progress = 5
            
            # Copy files
            data_dir = export_dir / "data"
            data_dir.mkdir(exist_ok=True)
            
            copied_count = 0
            for file in filtered_files:
                source_path = self.storage_path / file.relative_path
                if source_path.exists():
                    dest_path = data_dir / file.filename
                    # Handle duplicate filenames
                    if dest_path.exists():
                        stem = dest_path.stem
                        suffix = dest_path.suffix
                        counter = 1
                        while dest_path.exists():
                            dest_path = data_dir / f"{stem}_{counter}{suffix}"
                            counter += 1
                    
                    shutil.copy2(source_path, dest_path)
                    copied_count += 1
                
                if task and total_files > 0:
                    task.progress = 5 + int((copied_count / total_files) * 70)
            
            # Generate metadata
            if include_metadata:
                metadata = self._generate_metadata(dataset, filtered_files)
                metadata_path = export_dir / "metadata.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            if task:
                task.progress = 80
            
            # Package based on format
            if output_format == "zip":
                output_path = await self._create_zip(export_dir, export_name)
            elif output_format == "tar":
                output_path = await self._create_tar(export_dir, export_name)
            else:
                output_path = export_dir
            
            if task:
                task.status = TaskStatus.COMPLETED.value
                task.progress = 100
                task.completed_at = datetime.utcnow()
                task.output_result = {
                    "output_path": str(output_path),
                    "files_exported": copied_count,
                    "format": output_format,
                    "size_bytes": output_path.stat().st_size if output_path.is_file() else 0,
                }
            
            return output_path
            
        except Exception as e:
            if task:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
            raise
    
    def _apply_filters(self, files: List[DataFile], filters: Optional[Dict[str, Any]]) -> List[DataFile]:
        """Apply filters to file list."""
        if not filters:
            return files
        
        result = files
        
        if 'data_type' in filters:
            result = [f for f in result if f.data_type == filters['data_type']]
        
        if 'status' in filters:
            result = [f for f in result if f.status == filters['status']]
        
        if 'min_size' in filters:
            result = [f for f in result if f.file_size >= filters['min_size']]
        
        if 'max_size' in filters:
            result = [f for f in result if f.file_size <= filters['max_size']]
        
        if 'extension' in filters:
            ext = filters['extension']
            result = [f for f in result if f.filename.lower().endswith(ext.lower())]
        
        if 'limit' in filters:
            result = result[:filters['limit']]
        
        return result
    
    def _generate_metadata(self, dataset: Dataset, files: List[DataFile]) -> Dict[str, Any]:
        """Generate export metadata."""
        # Calculate statistics
        total_size = sum(f.file_size for f in files)
        
        type_counts = {}
        for f in files:
            type_counts[f.data_type] = type_counts.get(f.data_type, 0) + 1
        
        file_list = []
        for f in files:
            file_info = {
                "filename": f.filename,
                "relative_path": f.relative_path,
                "file_size": f.file_size,
                "file_type": f.file_type,
                "data_type": f.data_type,
            }
            if f.paired_text:
                file_info["paired_text"] = f.paired_text
            file_list.append(file_info)
        
        return {
            "export_info": {
                "dataset_name": dataset.name,
                "dataset_id": dataset.id,
                "export_time": datetime.utcnow().isoformat(),
                "total_files": len(files),
                "total_size": total_size,
                "type_distribution": type_counts,
            },
            "files": file_list,
        }
    
    async def _create_zip(self, source_dir: Path, name: str) -> Path:
        """Create ZIP archive."""
        output_path = self.exports_path / f"{name}.zip"
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zf.write(file_path, arcname)
        
        # Clean up source directory
        shutil.rmtree(source_dir, ignore_errors=True)
        
        return output_path
    
    async def _create_tar(self, source_dir: Path, name: str) -> Path:
        """Create TAR.GZ archive."""
        import tarfile
        
        output_path = self.exports_path / f"{name}.tar.gz"
        
        with tarfile.open(output_path, 'w:gz') as tf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    tf.add(file_path, arcname)
        
        shutil.rmtree(source_dir, ignore_errors=True)
        
        return output_path
    
    async def export_for_training(
        self,
        dataset: Dataset,
        files: List[DataFile],
        output_format: str = "jsonl",
        task: Optional[Task] = None,
    ) -> Path:
        """
        Export dataset in training-ready format.
        
        Creates JSONL files with image-text pairs for VLM training.
        """
        if task:
            task.status = TaskStatus.RUNNING.value
            task.started_at = datetime.utcnow()
        
        export_name = f"{dataset.name}_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        export_dir = self.exports_path / export_name
        export_dir.mkdir(parents=True, exist_ok=True)
        
        training_data = []
        
        for file in files:
            if file.paired_text:
                item = {
                    "id": file.id,
                    "image": file.relative_path,
                    "text": file.paired_text,
                    "metadata": {
                        "width": file.file_metadata.width if file.file_metadata else None,
                        "height": file.file_metadata.height if file.file_metadata else None,
                    }
                }
                training_data.append(item)
        
        # Write training data
        output_file = export_dir / "training_data.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in training_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        # Write stats
        stats = {
            "total_pairs": len(training_data),
            "dataset_id": dataset.id,
            "export_time": datetime.utcnow().isoformat(),
        }
        (export_dir / "stats.json").write_text(json.dumps(stats, indent=2))
        
        # Create ZIP
        zip_path = await self._create_zip(export_dir, export_name)
        
        if task:
            task.status = TaskStatus.COMPLETED.value
            task.progress = 100
            task.completed_at = datetime.utcnow()
            task.output_result = {
                "output_path": str(zip_path),
                "training_pairs": len(training_data),
            }
        
        return zip_path
    
    def list_exports(self) -> List[Dict[str, Any]]:
        """List all exports."""
        exports = []
        
        for path in self.exports_path.iterdir():
            if path.is_file() and (path.suffix in ['.zip', '.gz']):
                stat = path.stat()
                exports.append({
                    "name": path.stem,
                    "path": str(path),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                })
            elif path.is_dir():
                stat = path.stat()
                exports.append({
                    "name": path.name,
                    "path": str(path),
                    "type": "directory",
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                })
        
        return sorted(exports, key=lambda x: x['created_at'], reverse=True)
    
    def delete_export(self, export_name: str) -> bool:
        """Delete an export."""
        export_path = self.exports_path / export_name
        
        # Also check for ZIP/TAR versions
        for ext in ['.zip', '.tar.gz']:
            alt_path = self.exports_path / (export_name + ext)
            if alt_path.exists():
                alt_path.unlink()
                return True
        
        if export_path.exists() and export_path.is_dir():
            shutil.rmtree(export_path)
            return True
        
        return False


# Singleton
export_service = ExportService()
