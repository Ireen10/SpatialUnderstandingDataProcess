"""
AI-powered transformation script endpoints
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, APIKey
from app.services.script_execution import script_service

router = APIRouter(prefix="/transform", tags=["transform"])


class GenerateScriptRequest(BaseModel):
    """Request to generate transformation script."""
    source_format: str
    target_format: str
    sample_data: Optional[Dict[str, Any]] = None
    requirements: Optional[str] = None


class TestScriptRequest(BaseModel):
    """Request to test a script."""
    script: str
    test_data: Dict[str, Any]
    timeout: int = 30


class ExecuteScriptRequest(BaseModel):
    """Request to execute script on data."""
    script: Optional[str] = None
    script_name: Optional[str] = None  # Use saved script
    input_data: Dict[str, Any]
    save_script: bool = True
    timeout: int = 300


@router.post("/generate")
async def generate_transformation_script(
    request: GenerateScriptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate transformation script using AI.
    
    Describe your source format and target format in natural language,
    and optionally provide sample data. AI will generate a Python script.
    """
    # Get user's API key
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
            detail="Please configure your LLM API key first."
        )
    
    result = await script_service.generate_script(
        source_format=request.source_format,
        target_format=request.target_format,
        sample_data=request.sample_data,
        requirements=request.requirements,
        api_key=api_key_record.llm_api_key,
        base_url=api_key_record.llm_api_url,
        model=api_key_record.llm_model,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    # Update quota
    api_key_record.quota_used += 1
    await db.commit()
    
    return result


@router.post("/validate")
async def validate_script(
    script: str,
    current_user: User = Depends(get_current_user),
):
    """
    Validate script for security issues.
    
    Checks for dangerous operations and unauthorized modules.
    """
    result = script_service.validate_script_security(script)
    return result


@router.post("/test")
async def test_script(
    request: TestScriptRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Test script with sample data in sandbox.
    
    Runs the script in an isolated environment with the provided test data.
    """
    result = await script_service.test_script(
        script_code=request.script,
        test_data=request.test_data,
        timeout=request.timeout,
    )
    
    return result


@router.post("/execute")
async def execute_script(
    request: ExecuteScriptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute transformation script on data.
    
    Either provide script code directly or use a saved script by name.
    """
    # Get script code
    if request.script_name:
        script_code = script_service.get_script(request.script_name)
        if not script_code:
            raise HTTPException(status_code=404, detail="Script not found")
    elif request.script:
        script_code = request.script
    else:
        raise HTTPException(status_code=400, detail="Provide either script or script_name")
    
    result = await script_service.execute_script(
        script_code=script_code,
        input_data=request.input_data,
        script_name=request.script_name,
        timeout=request.timeout,
        save_script=request.save_script,
    )
    
    return result


@router.post("/generate-and-execute")
async def generate_and_execute(
    request: GenerateScriptRequest,
    test_first: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate script and execute in one step.
    
    1. AI generates transformation script
    2. Validates script security
    3. Tests with sample data (if test_first=True)
    4. Returns script and test result
    
    Use /execute endpoint with the returned script to run on actual data.
    """
    # Get API key
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
            detail="Please configure your LLM API key first."
        )
    
    # Generate script
    gen_result = await script_service.generate_script(
        source_format=request.source_format,
        target_format=request.target_format,
        sample_data=request.sample_data,
        requirements=request.requirements,
        api_key=api_key_record.llm_api_key,
        base_url=api_key_record.llm_api_url,
        model=api_key_record.llm_model,
    )
    
    if not gen_result["success"]:
        raise HTTPException(status_code=500, detail=gen_result.get("error"))
    
    # Update quota
    api_key_record.quota_used += 1
    await db.commit()
    
    script_code = gen_result["script"]
    
    # Validate security
    validation = script_service.validate_script_security(script_code)
    gen_result["validation"] = validation
    
    # Test with sample data if provided
    if test_first and request.sample_data:
        test_result = await script_service.test_script(
            script_code=script_code,
            test_data=request.sample_data,
        )
        gen_result["test_result"] = test_result
    
    return gen_result


@router.get("/scripts")
async def list_saved_scripts(
    current_user: User = Depends(get_current_user),
):
    """List all saved transformation scripts."""
    return {"scripts": script_service.list_saved_scripts()}


@router.get("/scripts/{script_name}")
async def get_saved_script(
    script_name: str,
    current_user: User = Depends(get_current_user),
):
    """Get saved script content."""
    script = script_service.get_script(script_name)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return {"name": script_name, "script": script}


@router.delete("/scripts/{script_name}")
async def delete_saved_script(
    script_name: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a saved script."""
    if script_service.delete_script(script_name):
        return {"message": "Script deleted"}
    raise HTTPException(status_code=404, detail="Script not found")