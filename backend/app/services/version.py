"""
Data version management service (DVC integration)
"""

import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

from app.core.config import settings
from app.models.dataset import Dataset
from loguru import logger


class VersionService:
    """Service for data version management using DVC or Git."""
    
    def __init__(self):
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
        self.versions_path = self.storage_path / "versions"
        self.versions_path.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.versions_path / "manifest.json"
        
        # Check if DVC is available
        self._dvc_available = self._check_dvc()
        self._git_available = self._check_git()
    
    def _check_dvc(self) -> bool:
        """Check if DVC is installed."""
        try:
            result = subprocess.run(
                ["dvc", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_git(self) -> bool:
        """Check if Git is installed."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load version manifest."""
        if self.manifest_file.exists():
            return json.loads(self.manifest_file.read_text())
        return {"versions": []}
    
    def _save_manifest(self, manifest: Dict[str, Any]):
        """Save version manifest."""
        self.manifest_file.write_text(json.dumps(manifest, indent=2))
    
    async def create_version(
        self,
        dataset: Dataset,
        version_name: str,
        description: Optional[str] = None,
        author: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new version snapshot of a dataset.
        
        Args:
            dataset: Dataset to version
            version_name: Version identifier (e.g., v1.0.0)
            description: Version description
            author: Author name
        
        Returns:
            Version info
        """
        manifest = self._load_manifest()
        
        # Check if version name already exists
        for v in manifest["versions"]:
            if v["dataset_id"] == dataset.id and v["version_name"] == version_name:
                raise ValueError(f"Version {version_name} already exists for this dataset")
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        version_id = f"{dataset.id}_{version_name}_{timestamp}"
        
        version_info = {
            "id": version_id,
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "version_name": version_name,
            "description": description,
            "author": author,
            "created_at": datetime.utcnow().isoformat(),
            "storage_type": "local",
            "files_count": 0,
            "total_size": 0,
            "checksum": None,
            "dvc_hash": None,
            "git_commit": None,
        }
        
        source_path = self.storage_path / dataset.storage_path
        version_path = self.versions_path / version_id
        
        if not source_path.exists():
            raise ValueError(f"Dataset path does not exist: {source_path}")
        
        # Create version snapshot
        try:
            # Copy files
            shutil.copytree(source_path, version_path)
            
            # Calculate stats
            total_size = 0
            files_count = 0
            for f in version_path.rglob('*'):
                if f.is_file():
                    total_size += f.stat().st_size
                    files_count += 1
            
            version_info["files_count"] = files_count
            version_info["total_size"] = total_size
            
            # Try DVC if available
            if self._dvc_available:
                try:
                    result = subprocess.run(
                        ["dvc", "add", str(version_path)],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd=str(self.storage_path)
                    )
                    if result.returncode == 0:
                        version_info["storage_type"] = "dvc"
                        # Parse DVC hash from .dvc file
                        dvc_file = str(version_path) + ".dvc"
                        if Path(dvc_file).exists():
                            dvc_data = json.loads(Path(dvc_file).read_text())
                            version_info["dvc_hash"] = dvc_data.get("outs", [{}])[0].get("md5")
                except Exception as e:
                    logger.warning(f"DVC add failed: {e}")
            
            # Try Git commit if available
            if self._git_available:
                try:
                    subprocess.run(
                        ["git", "add", "."],
                        capture_output=True,
                        timeout=30,
                        cwd=str(self.storage_path)
                    )
                    result = subprocess.run(
                        ["git", "commit", "-m", f"Version {version_name} of {dataset.name}"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=str(self.storage_path)
                    )
                    if result.returncode == 0:
                        # Get commit hash
                        result = subprocess.run(
                            ["git", "rev-parse", "HEAD"],
                            capture_output=True,
                            text=True,
                            timeout=10,
                            cwd=str(self.storage_path)
                        )
                        if result.returncode == 0:
                            version_info["git_commit"] = result.stdout.strip()
                            version_info["storage_type"] = "git"
                except Exception as e:
                    logger.warning(f"Git commit failed: {e}")
            
        except Exception as e:
            # Clean up on failure
            if version_path.exists():
                shutil.rmtree(version_path, ignore_errors=True)
            raise
        
        # Update manifest
        manifest["versions"].append(version_info)
        self._save_manifest(manifest)
        
        logger.info(f"Created version {version_name} for dataset {dataset.name}")
        
        return version_info
    
    async def restore_version(
        self,
        version_id: str,
        dataset: Dataset,
    ) -> Dict[str, Any]:
        """
        Restore dataset to a specific version.
        
        Args:
            version_id: Version ID to restore
            dataset: Target dataset
        
        Returns:
            Restore result
        """
        manifest = self._load_manifest()
        
        # Find version
        version_info = None
        for v in manifest["versions"]:
            if v["id"] == version_id:
                version_info = v
                break
        
        if not version_info:
            raise ValueError(f"Version not found: {version_id}")
        
        version_path = self.versions_path / version_id
        target_path = self.storage_path / dataset.storage_path
        
        if not version_path.exists():
            raise ValueError(f"Version data not found: {version_path}")
        
        # Backup current state
        if target_path.exists():
            backup_path = self.versions_path / f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            shutil.copytree(target_path, backup_path)
        
        # Restore
        if target_path.exists():
            shutil.rmtree(target_path)
        
        shutil.copytree(version_path, target_path)
        
        return {
            "restored": True,
            "version_id": version_id,
            "version_name": version_info["version_name"],
            "restored_at": datetime.utcnow().isoformat(),
        }
    
    def list_versions(
        self,
        dataset_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List all versions."""
        manifest = self._load_manifest()
        
        if dataset_id is not None:
            return [v for v in manifest["versions"] if v["dataset_id"] == dataset_id]
        
        return manifest["versions"]
    
    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Get version info."""
        manifest = self._load_manifest()
        
        for v in manifest["versions"]:
            if v["id"] == version_id:
                return v
        
        return None
    
    def delete_version(self, version_id: str) -> bool:
        """Delete a version snapshot."""
        manifest = self._load_manifest()
        
        for i, v in enumerate(manifest["versions"]):
            if v["id"] == version_id:
                version_path = self.versions_path / version_id
                
                # Remove DVC tracking if applicable
                if self._dvc_available:
                    dvc_file = Path(str(version_path) + ".dvc")
                    if dvc_file.exists():
                        dvc_file.unlink()
                
                # Remove version directory
                if version_path.exists():
                    shutil.rmtree(version_path, ignore_errors=True)
                
                # Update manifest
                manifest["versions"].pop(i)
                self._save_manifest(manifest)
                
                return True
        
        return False
    
    def compare_versions(
        self,
        version_id_1: str,
        version_id_2: str,
    ) -> Dict[str, Any]:
        """
        Compare two versions of a dataset.
        
        Returns differences in files.
        """
        v1 = self.get_version(version_id_1)
        v2 = self.get_version(version_id_2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        v1_path = self.versions_path / version_id_1
        v2_path = self.versions_path / version_id_2
        
        if not v1_path.exists() or not v2_path.exists():
            raise ValueError("Version data not found")
        
        # Get file lists
        v1_files = set(str(f.relative_to(v1_path)) for f in v1_path.rglob('*') if f.is_file())
        v2_files = set(str(f.relative_to(v2_path)) for f in v2_path.rglob('*') if f.is_file())
        
        added = v2_files - v1_files
        removed = v1_files - v2_files
        common = v1_files & v2_files
        
        # Check for modified files (by size for now)
        modified = []
        for f in common:
            v1_file = v1_path / f
            v2_file = v2_path / f
            
            if v1_file.stat().st_size != v2_file.stat().st_size:
                modified.append(f)
        
        return {
            "version_1": v1["version_name"],
            "version_2": v2["version_name"],
            "added": sorted(list(added)),
            "removed": sorted(list(removed)),
            "modified": sorted(modified),
            "unchanged": sorted(list(common - set(modified))),
            "stats": {
                "added_count": len(added),
                "removed_count": len(removed),
                "modified_count": len(modified),
                "unchanged_count": len(common) - len(modified),
            }
        }
    
    def get_version_info(self) -> Dict[str, Any]:
        """Get versioning system info."""
        return {
            "dvc_available": self._dvc_available,
            "git_available": self._git_available,
            "versions_path": str(self.versions_path),
            "total_versions": len(self.list_versions()),
        }


# Singleton
version_service = VersionService()
