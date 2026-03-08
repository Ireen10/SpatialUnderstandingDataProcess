"""
Backup service for data protection
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

from app.core.config import settings
from app.models.dataset import Dataset, DataFile


class BackupService:
    """Service for backing up data."""
    
    def __init__(self):
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
        self.backups_path = self.storage_path / "backups"
        self.backups_path.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.backups_path / "manifest.json"
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load backup manifest."""
        if self.manifest_file.exists():
            return json.loads(self.manifest_file.read_text())
        return {"backups": []}
    
    def _save_manifest(self, manifest: Dict[str, Any]):
        """Save backup manifest."""
        self.manifest_file.write_text(json.dumps(manifest, indent=2))
    
    def _calculate_checksum(self, path: Path) -> str:
        """Calculate MD5 checksum of a file or directory."""
        if path.is_file():
            return hashlib.md5(path.read_bytes()).hexdigest()
        elif path.is_dir():
            hasher = hashlib.md5()
            for file in sorted(path.rglob('*')):
                if file.is_file():
                    hasher.update(file.read_bytes())
            return hasher.hexdigest()
        return ""
    
    async def create_backup(
        self,
        dataset: Dataset,
        files: List[DataFile],
        backup_type: str = "full",
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a backup of a dataset.
        
        Args:
            dataset: Dataset to backup
            files: List of files to backup
            backup_type: Type of backup (full, incremental)
            description: Optional description
        
        Returns:
            Backup info
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{dataset.name}_{backup_type}_{timestamp}"
        backup_path = self.backups_path / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        manifest = self._load_manifest()
        
        # For incremental backup, check last backup
        last_backup = None
        if backup_type == "incremental" and manifest["backups"]:
            last_backup = manifest["backups"][-1]
        
        backup_info = {
            "id": len(manifest["backups"]) + 1,
            "name": backup_name,
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "type": backup_type,
            "created_at": datetime.utcnow().isoformat(),
            "description": description,
            "files_count": 0,
            "size_bytes": 0,
            "checksum": None,
        }
        
        # Copy files
        data_dir = backup_path / "data"
        data_dir.mkdir(exist_ok=True)
        
        copied_size = 0
        copied_count = 0
        
        for file in files:
            source_path = self.storage_path / file.relative_path
            
            if not source_path.exists():
                continue
            
            # For incremental, skip unchanged files
            if backup_type == "incremental" and last_backup:
                last_backup_path = self.backups_path / last_backup["name"] / "data" / file.filename
                if last_backup_path.exists():
                    source_hash = self._calculate_checksum(source_path)
                    last_hash = self._calculate_checksum(last_backup_path)
                    if source_hash == last_hash:
                        # Create hard link or copy from last backup
                        continue
            
            dest_path = data_dir / file.filename
            shutil.copy2(source_path, dest_path)
            copied_size += file.file_size
            copied_count += 1
        
        # Create backup metadata
        metadata = {
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "version": dataset.version,
            },
            "files": [
                {
                    "id": f.id,
                    "filename": f.filename,
                    "relative_path": f.relative_path,
                    "file_size": f.file_size,
                    "file_type": f.file_type,
                    "data_type": f.data_type,
                    "paired_text": f.paired_text,
                }
                for f in files
            ],
            "backup_info": backup_info,
        }
        
        (backup_path / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        # Update backup info
        backup_info["files_count"] = copied_count
        backup_info["size_bytes"] = copied_size
        backup_info["checksum"] = self._calculate_checksum(backup_path)
        
        # Update manifest
        manifest["backups"].append(backup_info)
        self._save_manifest(manifest)
        
        return backup_info
    
    async def restore_backup(
        self,
        backup_name: str,
        dataset: Dataset,
    ) -> Dict[str, Any]:
        """
        Restore a dataset from backup.
        
        Args:
            backup_name: Name of the backup to restore
            dataset: Target dataset (will be overwritten)
        
        Returns:
            Restore result
        """
        backup_path = self.backups_path / backup_name
        if not backup_path.exists():
            raise ValueError(f"Backup not found: {backup_name}")
        
        metadata = json.loads((backup_path / "metadata.json").read_text())
        
        # Restore files
        data_dir = backup_path / "data"
        target_dir = self.storage_path / dataset.storage_path
        
        # Clear target
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        restored_count = 0
        for file_info in metadata.get("files", []):
            source = data_dir / file_info["filename"]
            if source.exists():
                dest = target_dir / file_info["filename"]
                shutil.copy2(source, dest)
                restored_count += 1
        
        return {
            "restored": True,
            "backup_name": backup_name,
            "files_restored": restored_count,
            "restored_at": datetime.utcnow().isoformat(),
        }
    
    def list_backups(self, dataset_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all backups."""
        manifest = self._load_manifest()
        
        if dataset_id:
            return [b for b in manifest["backups"] if b["dataset_id"] == dataset_id]
        
        return manifest["backups"]
    
    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """Get info about a specific backup."""
        manifest = self._load_manifest()
        
        for backup in manifest["backups"]:
            if backup["name"] == backup_name:
                return backup
        
        return None
    
    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup."""
        manifest = self._load_manifest()
        
        for i, backup in enumerate(manifest["backups"]):
            if backup["name"] == backup_name:
                backup_path = self.backups_path / backup_name
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                
                manifest["backups"].pop(i)
                self._save_manifest(manifest)
                return True
        
        return False
    
    async def prune_old_backups(self, keep_count: int = 10) -> List[str]:
        """
        Remove old backups, keeping only the most recent ones.
        
        Args:
            keep_count: Number of backups to keep
        
        Returns:
            List of deleted backup names
        """
        manifest = self._load_manifest()
        
        if len(manifest["backups"]) <= keep_count:
            return []
        
        # Sort by created_at
        manifest["backups"].sort(key=lambda x: x["created_at"], reverse=True)
        
        deleted = []
        for backup in manifest["backups"][keep_count:]:
            backup_path = self.backups_path / backup["name"]
            if backup_path.exists():
                shutil.rmtree(backup_path)
            deleted.append(backup["name"])
        
        manifest["backups"] = manifest["backups"][:keep_count]
        self._save_manifest(manifest)
        
        return deleted
    
    def get_backup_size(self) -> int:
        """Get total size of all backups."""
        total_size = 0
        for backup_path in self.backups_path.iterdir():
            if backup_path.is_dir():
                for file in backup_path.rglob('*'):
                    if file.is_file():
                        total_size += file.stat().st_size
        return total_size


# Singleton
backup_service = BackupService()
