"""
Monitoring and audit endpoints
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user, get_admin_user
from app.models.user import User
from app.services.audit import audit_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class AuditLogRequest(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[dict] = None
    status: str = "success"


# ==================== Audit Logs ====================

@router.get("/audit-logs")
async def get_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    status: Optional[str] = None,
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
):
    """Get audit logs (admin sees all, users see their own)."""
    # Non-admin can only see their own logs
    if current_user.role != "admin":
        user_id = current_user.id
    
    start_time = datetime.utcnow() - timedelta(days=days)
    
    logs = audit_service.get_audit_logs(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        start_time=start_time,
        limit=limit,
    )
    
    return {"logs": logs, "total": len(logs)}


@router.post("/audit-logs")
async def create_audit_log(
    request: AuditLogRequest,
    current_user: User = Depends(get_current_user),
):
    """Create an audit log entry."""
    audit_service.log_action(
        user_id=current_user.id,
        action=request.action,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        details=request.details,
        status=request.status,
    )
    
    return {"message": "Audit log created"}


# ==================== Metrics ====================

@router.get("/metrics")
async def get_metrics(
    metric_name: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_admin_user),
):
    """Get system metrics (admin only)."""
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    metrics = audit_service.get_metrics(
        metric_name=metric_name,
        start_time=start_time,
    )
    
    return {"metrics": metrics, "total": len(metrics)}


@router.post("/metrics")
async def record_metric(
    metric_name: str = Query(...),
    value: float = Query(...),
    tags: Optional[dict] = None,
    current_user: User = Depends(get_admin_user),
):
    """Record a custom metric (admin only)."""
    audit_service.record_metric(
        metric_name=metric_name,
        value=value,
        tags=tags,
    )
    
    return {"message": "Metric recorded"}


# ==================== System Status ====================

@router.get("/health")
async def get_health():
    """Get system health status (public endpoint)."""
    return audit_service.get_health_status()


@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(get_admin_user),
):
    """Get system statistics (admin only)."""
    return audit_service.get_system_stats()


@router.get("/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(get_admin_user),
):
    """Get monitoring dashboard data (admin only)."""
    # Get recent audit logs summary
    logs_24h = audit_service.get_audit_logs(
        start_time=datetime.utcnow() - timedelta(hours=24),
        limit=1000,
    )
    
    # Count actions
    action_counts = {}
    for log in logs_24h:
        action = log.get("action", "unknown")
        action_counts[action] = action_counts.get(action, 0) + 1
    
    # Count resource types
    resource_counts = {}
    for log in logs_24h:
        resource = log.get("resource_type", "unknown")
        resource_counts[resource] = resource_counts.get(resource, 0) + 1
    
    # Get system stats
    system_stats = audit_service.get_system_stats()
    health = audit_service.get_health_status()
    
    return {
        "period": "24h",
        "total_actions": len(logs_24h),
        "action_breakdown": action_counts,
        "resource_breakdown": resource_counts,
        "system": system_stats,
        "health": health,
        "request_counts": audit_service._request_counts,
        "error_counts": audit_service._error_counts,
    }


# ==================== Cleanup ====================

@router.post("/cleanup")
async def cleanup_logs(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_admin_user),
):
    """Clean up old logs (admin only)."""
    result = audit_service.cleanup_old_logs(days=days)
    
    return {
        "message": f"Cleaned up logs older than {days} days",
        "deleted": result,
    }
