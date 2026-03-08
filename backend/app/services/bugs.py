"""
Data quality and bug marking service
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.core.config import settings
from app.models.dataset import DataFile


class BugType(str, Enum):
    FORMAT_ERROR = "format_error"
    ANNOTATION_ERROR = "annotation_error"
    DATA_CORRUPTED = "data_corrupted"
    MISSING_PAIR = "missing_pair"
    INVALID_METADATA = "invalid_metadata"
    DUPLICATE = "duplicate"
    OTHER = "other"


class BugStatus(str, Enum):
    REPORTED = "reported"
    CONFIRMED = "confirmed"
    FIXING = "fixing"
    FIXED = "fixed"
    IGNORED = "ignored"


class DataBugService:
    """Service for marking and fixing data bugs."""
    
    def __init__(self):
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
        self.bugs_path = self.storage_path / "bugs"
        self.bugs_path.mkdir(parents=True, exist_ok=True)
        self.bugs_file = self.bugs_path / "reported_bugs.json"
    
    def _load_bugs(self) -> List[Dict[str, Any]]:
        """Load reported bugs."""
        if self.bugs_file.exists():
            return json.loads(self.bugs_file.read_text())
        return []
    
    def _save_bugs(self, bugs: List[Dict[str, Any]]):
        """Save bugs to file."""
        self.bugs_file.write_text(json.dumps(bugs, indent=2, ensure_ascii=False))
    
    def report_bug(
        self,
        file_id: int,
        bug_type: str,
        description: str,
        severity: str = "medium",
        reported_by: int = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Report a bug in data file.
        
        Args:
            file_id: ID of the problematic file
            bug_type: Type of bug
            description: Description of the problem
            severity: Severity level (low, medium, high, critical)
            reported_by: User ID who reported
            metadata: Additional metadata
        
        Returns:
            Bug report
        """
        bugs = self._load_bugs()
        
        bug_report = {
            "id": len(bugs) + 1,
            "file_id": file_id,
            "bug_type": bug_type,
            "description": description,
            "severity": severity,
            "status": BugStatus.REPORTED.value,
            "reported_by": reported_by,
            "reported_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "fix_suggestion": None,
            "fixed_at": None,
            "fixed_by": None,
        }
        
        bugs.append(bug_report)
        self._save_bugs(bugs)
        
        return bug_report
    
    def update_bug_status(
        self,
        bug_id: int,
        status: str,
        fix_suggestion: Optional[str] = None,
        fixed_by: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update bug status."""
        bugs = self._load_bugs()
        
        for bug in bugs:
            if bug["id"] == bug_id:
                bug["status"] = status
                bug["updated_at"] = datetime.utcnow().isoformat()
                
                if fix_suggestion:
                    bug["fix_suggestion"] = fix_suggestion
                
                if status == BugStatus.FIXED.value:
                    bug["fixed_at"] = datetime.utcnow().isoformat()
                    bug["fixed_by"] = fixed_by
                
                self._save_bugs(bugs)
                return bug
        
        return None
    
    def get_bug(self, bug_id: int) -> Optional[Dict[str, Any]]:
        """Get bug by ID."""
        bugs = self._load_bugs()
        for bug in bugs:
            if bug["id"] == bug_id:
                return bug
        return None
    
    def list_bugs(
        self,
        file_id: Optional[int] = None,
        bug_type: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List bugs with optional filters."""
        bugs = self._load_bugs()
        
        if file_id is not None:
            bugs = [b for b in bugs if b["file_id"] == file_id]
        if bug_type:
            bugs = [b for b in bugs if b["bug_type"] == bug_type]
        if status:
            bugs = [b for b in bugs if b["status"] == status]
        if severity:
            bugs = [b for b in bugs if b["severity"] == severity]
        
        return bugs
    
    def get_bug_statistics(self) -> Dict[str, Any]:
        """Get bug statistics."""
        bugs = self._load_bugs()
        
        stats = {
            "total": len(bugs),
            "by_type": {},
            "by_status": {},
            "by_severity": {},
        }
        
        for bug in bugs:
            # By type
            bug_type = bug["bug_type"]
            stats["by_type"][bug_type] = stats["by_type"].get(bug_type, 0) + 1
            
            # By status
            status = bug["status"]
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # By severity
            severity = bug["severity"]
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
        
        return stats
    
    def delete_bug(self, bug_id: int) -> bool:
        """Delete a bug report."""
        bugs = self._load_bugs()
        
        for i, bug in enumerate(bugs):
            if bug["id"] == bug_id:
                bugs.pop(i)
                self._save_bugs(bugs)
                return True
        
        return False
    
    async def analyze_file_issues(
        self,
        data_file: DataFile,
        file_path: Path,
    ) -> List[Dict[str, Any]]:
        """
        Analyze a file for potential issues.
        
        Returns list of detected issues.
        """
        issues = []
        
        if not file_path.exists():
            issues.append({
                "type": BugType.DATA_CORRUPTED.value,
                "description": "File does not exist on disk",
                "severity": "high",
            })
            return issues
        
        # Check file integrity
        if data_file.file_size > 0:
            actual_size = file_path.stat().st_size
            if actual_size != data_file.file_size:
                issues.append({
                    "type": BugType.DATA_CORRUPTED.value,
                    "description": f"File size mismatch: expected {data_file.file_size}, actual {actual_size}",
                    "severity": "medium",
                })
        
        # Check for missing paired text
        if data_file.data_type in ["image", "video"]:
            if not data_file.paired_text:
                # Check if there's a matching text file
                text_file = file_path.with_suffix('.txt')
                json_file = file_path.with_suffix('.json')
                
                if not text_file.exists() and not json_file.exists():
                    issues.append({
                        "type": BugType.MISSING_PAIR.value,
                        "description": "No paired text/annotation file found",
                        "severity": "low",
                    })
        
        # Check for common format issues
        if data_file.file_type.startswith('image/'):
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    img.verify()
            except Exception as e:
                issues.append({
                    "type": BugType.FORMAT_ERROR.value,
                    "description": f"Image format error: {str(e)}",
                    "severity": "high",
                })
        
        elif data_file.file_type.startswith('video/'):
            try:
                import cv2
                cap = cv2.VideoCapture(str(file_path))
                if not cap.isOpened():
                    issues.append({
                        "type": BugType.FORMAT_ERROR.value,
                        "description": "Video file cannot be opened",
                        "severity": "high",
                    })
                cap.release()
            except Exception as e:
                issues.append({
                    "type": BugType.FORMAT_ERROR.value,
                    "description": f"Video format error: {str(e)}",
                    "severity": "medium",
                })
        
        elif data_file.file_type == 'application/json':
            try:
                json.loads(file_path.read_text())
            except json.JSONDecodeError as e:
                issues.append({
                    "type": BugType.FORMAT_ERROR.value,
                    "description": f"JSON parse error: {str(e)}",
                    "severity": "high",
                })
        
        return issues


# Singleton
bug_service = DataBugService()
