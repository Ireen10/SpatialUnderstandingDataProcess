"""
Logging and monitoring service
"""

import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import asyncio

from loguru import logger
from app.core.config import settings


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditLogService:
    """Service for audit logging and system monitoring."""
    
    def __init__(self):
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
        self.logs_path = self.storage_path / "logs"
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        self.audit_file = self.logs_path / "audit.jsonl"
        self.metrics_file = self.logs_path / "metrics.jsonl"
        
        # In-memory metrics cache
        self._metrics_cache: Dict[str, List[float]] = defaultdict(list)
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._error_counts: Dict[str, int] = defaultdict(int)
    
    def log_action(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
    ):
        """
        Log an audit action.
        
        Args:
            user_id: ID of user performing action
            action: Action type (create, read, update, delete, etc.)
            resource_type: Type of resource (dataset, file, user, etc.)
            resource_id: ID of resource
            details: Additional details
            ip_address: Client IP
            user_agent: Client user agent
            status: Action status (success, failed)
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status": status,
        }
        
        # Append to audit log
        with open(self.audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"AUDIT: {action} {resource_type}:{resource_id} by user:{user_id} - {status}")
    
    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit logs with filters."""
        if not self.audit_file.exists():
            return []
        
        logs = []
        with open(self.audit_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    logs.append(entry)
                except:
                    continue
        
        # Apply filters
        if user_id is not None:
            logs = [l for l in logs if l.get("user_id") == user_id]
        if action:
            logs = [l for l in logs if l.get("action") == action]
        if resource_type:
            logs = [l for l in logs if l.get("resource_type") == resource_type]
        if resource_id is not None:
            logs = [l for l in logs if l.get("resource_id") == resource_id]
        if status:
            logs = [l for l in logs if l.get("status") == status]
        if start_time:
            logs = [l for l in logs if datetime.fromisoformat(l["timestamp"]) >= start_time]
        if end_time:
            logs = [l for l in logs if datetime.fromisoformat(l["timestamp"]) <= end_time]
        
        # Sort by timestamp descending
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return logs[:limit]
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ):
        """Record a metric value."""
        metric_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "metric": metric_name,
            "value": value,
            "tags": tags or {},
        }
        
        # Append to metrics log
        with open(self.metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metric_entry) + '\n')
        
        # Update cache
        self._metrics_cache[metric_name].append(value)
        if len(self._metrics_cache[metric_name]) > 1000:
            self._metrics_cache[metric_name] = self._metrics_cache[metric_name][-1000:]
    
    def get_metrics(
        self,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get recorded metrics."""
        if not self.metrics_file.exists():
            return []
        
        metrics = []
        with open(self.metrics_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    metrics.append(entry)
                except:
                    continue
        
        # Apply filters
        if metric_name:
            metrics = [m for m in metrics if m.get("metric") == metric_name]
        if start_time:
            metrics = [m for m in metrics if datetime.fromisoformat(m["timestamp"]) >= start_time]
        if end_time:
            metrics = [m for m in metrics if datetime.fromisoformat(m["timestamp"]) <= end_time]
        
        return metrics
    
    def increment_request_count(self, endpoint: str):
        """Increment request counter for an endpoint."""
        self._request_counts[endpoint] += 1
    
    def increment_error_count(self, error_type: str):
        """Increment error counter."""
        self._error_counts[error_type] += 1
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        import psutil
        import platform
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "system": {
                    "platform": platform.system(),
                    "python_version": platform.python_version(),
                    "hostname": platform.node(),
                },
                "resources": {
                    "cpu_percent": cpu_percent,
                    "memory_total": memory.total,
                    "memory_used": memory.used,
                    "memory_percent": memory.percent,
                    "disk_total": disk.total,
                    "disk_used": disk.used,
                    "disk_percent": disk.percent,
                },
                "requests": dict(self._request_counts),
                "errors": dict(self._error_counts),
                "uptime": self._get_uptime(),
            }
        except ImportError:
            # psutil not installed
            return {
                "system": {
                    "platform": platform.system(),
                    "python_version": platform.python_version(),
                },
                "requests": dict(self._request_counts),
                "errors": dict(self._error_counts),
            }
    
    def _get_uptime(self) -> Optional[float]:
        """Get system uptime in seconds."""
        try:
            import psutil
            return time.time() - psutil.boot_time()
        except:
            return None
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        stats = self.get_system_stats()
        
        health = {
            "status": "healthy",
            "checks": {},
        }
        
        # Check memory
        memory_percent = stats.get("resources", {}).get("memory_percent", 0)
        if memory_percent > 90:
            health["status"] = "warning"
            health["checks"]["memory"] = {"status": "warning", "usage": f"{memory_percent}%"}
        else:
            health["checks"]["memory"] = {"status": "ok", "usage": f"{memory_percent}%"}
        
        # Check disk
        disk_percent = stats.get("resources", {}).get("disk_percent", 0)
        if disk_percent > 90:
            health["status"] = "warning"
            health["checks"]["disk"] = {"status": "warning", "usage": f"{disk_percent}%"}
        else:
            health["checks"]["disk"] = {"status": "ok", "usage": f"{disk_percent}%"}
        
        # Check error rate
        total_requests = sum(self._request_counts.values())
        total_errors = sum(self._error_counts.values())
        if total_requests > 0:
            error_rate = total_errors / total_requests
            if error_rate > 0.1:  # More than 10% errors
                health["status"] = "warning"
                health["checks"]["error_rate"] = {"status": "warning", "rate": f"{error_rate:.2%}"}
            else:
                health["checks"]["error_rate"] = {"status": "ok", "rate": f"{error_rate:.2%}"}
        
        return health
    
    def cleanup_old_logs(self, days: int = 30) -> Dict[str, int]:
        """Clean up logs older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        cleaned = {"audit": 0, "metrics": 0}
        
        # Clean audit logs
        if self.audit_file.exists():
            new_lines = []
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if datetime.fromisoformat(entry["timestamp"]) >= cutoff:
                            new_lines.append(line)
                        else:
                            cleaned["audit"] += 1
                    except:
                        continue
            
            with open(self.audit_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        
        # Clean metrics logs
        if self.metrics_file.exists():
            new_lines = []
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if datetime.fromisoformat(entry["timestamp"]) >= cutoff:
                            new_lines.append(line)
                        else:
                            cleaned["metrics"] += 1
                    except:
                        continue
            
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        
        return cleaned


# Singleton
audit_service = AuditLogService()
