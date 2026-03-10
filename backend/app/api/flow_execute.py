"""流程执行 REST API - v3.0 端口化架构"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/flows", tags=["flows"])


class FlowExecuteRequest(BaseModel):
    """流程执行请求"""
    flow_id: str
    flow_definition: Dict[str, Any]
    inputs: Dict[str, Any]


class FlowExecuteResponse(BaseModel):
    """流程执行响应"""
    success: bool
    flow_id: str
    outputs: Dict[str, Any]
    message: str = ""


class FlowDefinition(BaseModel):
    """流程定义"""
    flow_id: str
    flow_inputs: List[Dict[str, Any]]
    flow_outputs: List[Dict[str, Any]]
    modules: List[Dict[str, Any]]
    connections: List[Dict[str, str]]


class FlowMeta(BaseModel):
    """流程元数据"""
    flow_id: str
    name: str
    created_at: str = ""
    updated_at: str = ""


class FlowListResponse(BaseModel):
    """流程列表响应"""
    flows: List[FlowMeta]


@router.post("/execute", response_model=FlowExecuteResponse)
async def execute_flow(request: FlowExecuteRequest):
    """
    执行流程
    
    **请求体**:
    ```json
    {
        "flow_id": "flow_001",
        "flow_definition": {
            "flow_inputs": [{"port": "start", "type": "str"}],
            "flow_outputs": [{"port": "result", "type": "dict"}],
            "modules": [{"id": "m1", "module": "test_module"}],
            "connections": [{"from": "flow:start:0", "to": "m1:input:0"}]
        },
        "inputs": {"start": "test"}
    }
    ```
    
    **响应**:
    ```json
    {
        "success": true,
        "flow_id": "flow_001",
        "outputs": {"result": {...}},
        "message": "流程执行成功"
    }
    ```
    """
    try:
        logger.info(f"执行流程：{request.flow_id}")
        
        # 延迟导入防止循环引用
        from app.services.flow_execution_service import get_flow_service
        
        # 获取服务实例
        service = get_flow_service()
        
        # 执行流程
        result = await service.execute_flow(
            flow_id=request.flow_id,
            flow_definition=request.flow_definition,
            inputs=request.inputs
        )
        
        if result.get("success"):
            return FlowExecuteResponse(
                success=True,
                flow_id=request.flow_id,
                outputs=result.get("outputs", {}),
                message=result.get("message", "流程执行成功")
            )
        else:
            return FlowExecuteResponse(
                success=False,
                flow_id=request.flow_id,
                outputs={},
                message=result.get("message", "流程执行失败")
            )
            
    except Exception as e:
        logger.error(f"流程执行失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_flow(flow_def: FlowDefinition):
    """
    创建/保存流程
    
    **流程定义**:
    ```json
    {
        "flow_id": "flow_001",
        "flow_inputs": [...],
        "flow_outputs": [...],
        "modules": [...],
        "connections": [...]
    }
    ```
    """
    try:
        from app.services.flow_storage import FlowStorageService
        import os
        
        # 创建存储服务
        storage_root = os.environ.get("FLOW_STORAGE_ROOT", "workspaces/flows")
        storage = FlowStorageService(storage_root)
        
        # 保存流程
        flow_dict = flow_def.dict()
        success = storage.save_flow(flow_def.flow_id, flow_dict)
        
        if success:
            return {
                "success": True,
                "flow_id": flow_def.flow_id,
                "message": "流程已创建"
            }
        else:
            raise HTTPException(status_code=500, detail="保存流程失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建流程失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{flow_id}")
async def get_flow(flow_id: str):
    """获取流程定义"""
    try:
        from app.services.flow_storage import FlowStorageService
        import os
        
        storage_root = os.environ.get("FLOW_STORAGE_ROOT", "workspaces/flows")
        storage = FlowStorageService(storage_root)
        
        flow_def = storage.load_flow(flow_id)
        
        if flow_def is None:
            raise HTTPException(status_code=404, detail="流程不存在")
        
        return flow_def
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取流程失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=FlowListResponse)
async def list_flows():
    """获取所有流程列表"""
    try:
        from app.services.flow_storage import FlowStorageService
        import os
        
        storage_root = os.environ.get("FLOW_STORAGE_ROOT", "workspaces/flows")
        storage = FlowStorageService(storage_root)
        
        flow_metas = storage.list_flows()
        
        return FlowListResponse(flows=flow_metas)
        
    except Exception as e:
        logger.error(f"获取流程列表失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{flow_id}")
async def delete_flow(flow_id: str):
    """删除流程"""
    try:
        from app.services.flow_storage import FlowStorageService
        import os
        
        storage_root = os.environ.get("FLOW_STORAGE_ROOT", "workspaces/flows")
        storage = FlowStorageService(storage_root)
        
        success = storage.delete_flow(flow_id)
        
        if success:
            return {
                "success": True,
                "message": "流程已删除"
            }
        else:
            raise HTTPException(status_code=404, detail="流程不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除流程失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
