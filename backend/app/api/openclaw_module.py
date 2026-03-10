"""OpenClaw 模块创建和反馈 API - v4.0

支持：
- 功能模块创建
- 分支模块创建
- 模块编辑（版本管理）
- 模块反馈处理
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/openclaw", tags=["openclaw"])

# ========== 请求模型 ==========

class PortDefinition(BaseModel):
    """端口定义"""
    name: str
    description: str = ""


class ParamDefinition(BaseModel):
    """参数定义"""
    name: str
    default: Any = None
    description: str = ""


class BranchCondition(BaseModel):
    """分支条件"""
    id: str
    description: str


class CreateFunctionModuleRequest(BaseModel):
    """创建功能模块请求"""
    module_name: str
    description: str
    inputs: List[PortDefinition]
    outputs: List[PortDefinition]
    parameters: List[ParamDefinition] = []


class CreateBranchModuleRequest(BaseModel):
    """创建分支模块请求"""
    module_name: str
    description: str
    input: PortDefinition
    conditions: List[BranchCondition]


class EditModuleRequest(BaseModel):
    """编辑模块请求"""
    module_id: str
    current_version: int
    edit_description: str


class ModuleFeedbackRequest(BaseModel):
    """模块反馈请求"""
    module_id: str
    version: int
    error_type: str
    error_message: str
    traceback: str
    user_description: str = ""
    callback_url: str = ""


# ========== API 端点 ==========

@router.post("/modules/function")
async def create_function_module(request: CreateFunctionModuleRequest):
    """
    创建功能模块
    
    功能模块：处理数据的核心模块，有输入端口、输出端口和可变参数。
    """
    try:
        from app.services.openclaw_client import openclaw_client
        
        result = await openclaw_client.create_function_module(request)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "创建失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建功能模块失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modules/branch")
async def create_branch_module(request: CreateBranchModuleRequest):
    """
    创建分支模块
    
    分支模块：条件分流，数据透传，必有兜底分支（default）。
    条件按列表顺序确定优先级。
    """
    try:
        from app.services.openclaw_client import openclaw_client
        
        result = await openclaw_client.create_branch_module(request)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "创建失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建分支模块失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modules/edit")
async def edit_module(request: EditModuleRequest):
    """
    编辑模块
    
    编辑模块会创建新版本，保留历史版本。
    用户可在流程中选择使用哪个版本。
    """
    try:
        from app.services.openclaw_client import openclaw_client
        
        result = await openclaw_client.edit_module(request)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "编辑失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"编辑模块失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modules/feedback")
async def submit_feedback(request: ModuleFeedbackRequest):
    """
    提交模块反馈
    
    用户反馈模块问题，OpenClaw 分析并修复，创建新版本。
    """
    try:
        from app.services.openclaw_client import openclaw_client
        
        result = await openclaw_client.submit_feedback(request)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "反馈处理失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交反馈失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== 模块仓库管理 ==========

@router.get("/modules")
async def list_modules():
    """获取模块列表"""
    import os
    from pathlib import Path
    import json
    
    try:
        modules_root = Path(os.environ.get("MODULES_ROOT", "/mnt/d/GithubRepo/SpatialUnderstandingDataProcess/modules"))
        
        if not modules_root.exists():
            return {"modules": []}
        
        modules = []
        for module_dir in modules_root.iterdir():
            if module_dir.is_dir() and module_dir.name.startswith("mod_"):
                metadata_file = module_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    modules.append(metadata)
        
        return {"modules": modules}
    except Exception as e:
        logger.error(f"获取模块列表失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules/{module_id}")
async def get_module(module_id: str):
    """获取模块详情"""
    import os
    from pathlib import Path
    import json
    
    try:
        modules_root = Path(os.environ.get("MODULES_ROOT", "/mnt/d/GithubRepo/SpatialUnderstandingDataProcess/modules"))
        module_dir = modules_root / module_id
        
        if not module_dir.exists():
            raise HTTPException(status_code=404, detail=f"模块 {module_id} 不存在")
        
        metadata_file = module_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            return metadata
        else:
            raise HTTPException(status_code=404, detail=f"模块 {module_id} 元数据不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模块详情失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/modules/{module_id}/versions/{version}")
async def delete_module_version(module_id: str, version: int):
    """
    删除模块版本
    
    注意：不能删除正在被流程引用的版本
    """
    import os
    from pathlib import Path
    import shutil
    
    try:
        modules_root = Path(os.environ.get("MODULES_ROOT", "/mnt/d/GithubRepo/SpatialUnderstandingDataProcess/modules"))
        version_dir = modules_root / module_id / f"v{version}"
        
        if not version_dir.exists():
            raise HTTPException(status_code=404, detail=f"版本 v{version} 不存在")
        
        # TODO: 检查是否有流程引用此版本
        # 目前直接删除
        
        shutil.rmtree(version_dir)
        
        return {"success": True, "message": f"版本 v{version} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除模块版本失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
