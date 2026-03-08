"""
Data bug marking and fixing endpoints
"""

from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import DataFile, Dataset
from app.services.bugs import bug_service, BugType, BugStatus
from app.services.ai import get_ai_service

router = APIRouter(prefix="/bugs", tags=["bugs"])


class BugReportRequest(BaseModel):
    file_id: int
    bug_type: str
    description: str
    severity: str = "medium"  # low, medium, high, critical
    metadata: Optional[dict] = None


class BugStatusUpdate(BaseModel):
    status: str
    fix_suggestion: Optional[str] = None


class BulkReportRequest(BaseModel):
    file_ids: List[int]
    bug_type: str
    description: str
    severity: str = "medium"


@router.post("")
async def report_bug(
    request: BugReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Report a bug in a data file."""
    # Verify file exists and user has access
    result = await db.execute(
        select(DataFile)
        .options(selectinload(DataFile.dataset))
        .where(DataFile.id == request.file_id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.dataset.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate bug type
    valid_types = [t.value for t in BugType]
    if request.bug_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid bug type. Valid types: {valid_types}"
        )
    
    bug = bug_service.report_bug(
        file_id=request.file_id,
        bug_type=request.bug_type,
        description=request.description,
        severity=request.severity,
        reported_by=current_user.id,
        metadata=request.metadata,
    )
    
    return bug


@router.post("/bulk")
async def bulk_report_bugs(
    request: BulkReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Report the same bug for multiple files."""
    reported = []
    
    for file_id in request.file_ids:
        result = await db.execute(
            select(DataFile)
            .options(selectinload(DataFile.dataset))
            .where(DataFile.id == file_id)
        )
        file = result.scalar_one_or_none()
        
        if file and file.dataset.user_id == current_user.id:
            bug = bug_service.report_bug(
                file_id=file_id,
                bug_type=request.bug_type,
                description=request.description,
                severity=request.severity,
                reported_by=current_user.id,
            )
            reported.append(bug)
    
    return {"reported": len(reported), "bugs": reported}


@router.get("")
async def list_bugs(
    file_id: Optional[int] = None,
    bug_type: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List reported bugs with optional filters."""
    bugs = bug_service.list_bugs(
        file_id=file_id,
        bug_type=bug_type,
        status=status,
        severity=severity,
    )
    return {"bugs": bugs}


@router.get("/statistics")
async def get_bug_statistics(
    current_user: User = Depends(get_current_user),
):
    """Get bug statistics."""
    return bug_service.get_bug_statistics()


@router.get("/{bug_id}")
async def get_bug(
    bug_id: int,
    current_user: User = Depends(get_current_user),
):
    """Get bug details."""
    bug = bug_service.get_bug(bug_id)
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    return bug


@router.patch("/{bug_id}")
async def update_bug_status(
    bug_id: int,
    request: BugStatusUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update bug status."""
    valid_statuses = [s.value for s in BugStatus]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid statuses: {valid_statuses}"
        )
    
    bug = bug_service.update_bug_status(
        bug_id=bug_id,
        status=request.status,
        fix_suggestion=request.fix_suggestion,
        fixed_by=current_user.id if request.status == "fixed" else None,
    )
    
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    return bug


@router.delete("/{bug_id}")
async def delete_bug(
    bug_id: int,
    current_user: User = Depends(get_current_user),
):
    """Delete a bug report."""
    if bug_service.delete_bug(bug_id):
        return {"message": "Bug deleted"}
    raise HTTPException(status_code=404, detail="Bug not found")


@router.post("/{bug_id}/analyze")
async def analyze_bug_with_ai(
    bug_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Use AI to analyze bug and suggest fix."""
    bug = bug_service.get_bug(bug_id)
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    # Get file info
    result = await db.execute(
        select(DataFile)
        .options(selectinload(DataFile.dataset), selectinload(DataFile.file_metadata))
        .where(DataFile.id == bug["file_id"])
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get AI service
    result = await db.execute(
        select(User).where(User.id == current_user.id)
    )
    
    # Try to get AI analysis
    from app.models.user import APIKey
    result = await db.execute(
        select(APIKey).where(
            APIKey.user_id == current_user.id,
            APIKey.is_active == True
        ).order_by(APIKey.created_at.desc())
    )
    api_key_record = result.scalar_one_or_none()
    
    if not api_key_record or not api_key_record.llm_api_key:
        raise HTTPException(
            status_code=400,
            detail="No AI API key configured. Please configure your API key to use AI analysis."
        )
    
    service = get_ai_service(
        api_key=api_key_record.llm_api_key,
        base_url=api_key_record.llm_api_url,
        model=api_key_record.llm_model,
    )
    
    # Build analysis prompt
    file_info = {
        "filename": file.filename,
        "file_type": file.file_type,
        "data_type": file.data_type,
        "file_size": file.file_size,
    }
    
    if file.file_metadata:
        file_info["metadata"] = {
            "width": file.file_metadata.width,
            "height": file.file_metadata.height,
            "duration": file.file_metadata.duration,
        }
    
    analysis = await service.chat(
        message=f"""Analyze this data bug and suggest a fix:

Bug Type: {bug['bug_type']}
Description: {bug['description']}
Severity: {bug['severity']}

File Info:
{json.dumps(file_info, indent=2)}

Please provide:
1. Root cause analysis
2. Step-by-step fix suggestion
3. Prevention recommendations""",
        system_prompt="You are a data quality expert. Provide actionable analysis and fix suggestions.",
    )
    
    # Update bug with suggestion
    bug_service.update_bug_status(
        bug_id=bug_id,
        status=bug["status"],
        fix_suggestion=analysis,
    )
    
    return {
        "bug_id": bug_id,
        "analysis": analysis,
    }


@router.post("/files/{file_id}/scan")
async def scan_file_for_issues(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Scan a file for potential issues."""
    result = await db.execute(
        select(DataFile)
        .options(selectinload(DataFile.dataset))
        .where(DataFile.id == file_id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.dataset.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_path = Path(settings.DATA_STORAGE_PATH) / file.relative_path
    
    issues = await bug_service.analyze_file_issues(file, file_path)
    
    # Auto-report found issues
    reported = []
    for issue in issues:
        bug = bug_service.report_bug(
            file_id=file_id,
            bug_type=issue["type"],
            description=issue["description"],
            severity=issue["severity"],
            reported_by=current_user.id,
        )
        reported.append(bug)
    
    return {
        "file_id": file_id,
        "issues_found": len(issues),
        "reported_bugs": reported,
    }


import json
