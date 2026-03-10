"""OpenClaw 模块创建和反馈 API"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/openclaw", tags=["openclaw"])

class CreateModuleRequest(BaseModel):
    module_name: str
    description: str
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    parameters: List[Dict[str, Any]]
    workflow_root: str = ""

class SubmitFeedbackRequest(BaseModel):
    module_name: str
    error_type: str
    error_message: str
    traceback: str
    user_description: str = ""
    callback_url: str = ""

@router.post("/modules/create")
async def create_module(request: CreateModuleRequest):
    """调用 OpenClaw 创建模块"""
    try:
        from app.services.openclaw_client import openclaw_client
        
        workflow_root = request.workflow_root or os.environ.get("WORKFLOW_MODULES_ROOT", "workspaces/templates")
        result = await openclaw_client.create_module(
            module_name=request.module_name,
            description=request.description,
            inputs=request.inputs,
            outputs=request.outputs,
            parameters=request.parameters,
            workflow_root=workflow_root
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "创建失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建模块失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/modules/feedback")
async def submit_feedback(request: SubmitFeedbackRequest):
    """提交模块反馈"""
    try:
        from app.services.openclaw_client import openclaw_client
        
        result = await openclaw_client.submit_feedback(
            module_name=request.module_name,
            error_type=request.error_type,
            error_message=request.error_message,
            traceback=request.traceback,
            user_description=request.user_description,
            callback_url=request.callback_url
        )
        
        return result
    except Exception as e:
        logger.error(f"提交反馈失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
