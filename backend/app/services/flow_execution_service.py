"""流程执行服务 - v3.0 端口化架构"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.services.workflow_executor_v3 import WorkflowExecutor
from app.services.module_loader_service import ModuleLoaderService
import logging

logger = logging.getLogger(__name__)

class FlowExecutionService:
    """流程执行服务 - 服务层封装"""
    
    def __init__(self, workflow_root: Optional[str] = None):
        """
        初始化服务
        
        Args:
            workflow_root: 流程模块根目录，默认使用环境变量或默认路径
        """
        if not workflow_root:
            workflow_root = os.environ.get(
                "WORKFLOW_MODULES_ROOT",
                str(Path(__file__).parent.parent.parent / "workspaces" / "templates")
            )
        self.workflow_root = Path(workflow_root)
        self.module_loader = ModuleLoaderService(self.workflow_root)
        logger.info(f"流程执行服务已初始化：{self.workflow_root}")
    
    async def execute_flow(
        self,
        flow_id: str,
        flow_definition: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行流程
        
        Args:
            flow_id: 流程 ID
            flow_definition: 流程定义 JSON
            inputs: 流程输入值
        
        Returns:
            流程输出值
        
        流程定义格式:
        {
            "flow_id": "flow_001",
            "flow_inputs": [{"port": "start", "type": "str"}],
            "flow_outputs": [{"port": "result", "type": "dict"}],
            "modules": [
                {"id": "m1", "module": "number_input", "params": {...}}
            ],
            "connections": [
                {"from": "flow:start:0", "to": "m1:numbers:1"}
            ]
        }
        """
        logger.info(f"开始执行流程：{flow_id}")
        
        try:
            # 创建流程执行器
            executor = WorkflowExecutor(flow_id)
            
            # 设置流程端口
            flow_inputs = flow_definition.get("flow_inputs", [])
            flow_outputs = flow_definition.get("flow_outputs", [])
            executor.set_flow_ports(flow_inputs, flow_outputs)
            
            # 加载并注册模块
            modules_def = flow_definition.get("modules", [])
            for module_def in modules_def:
                module_id = module_def["id"]
                module_name = module_def["module"]
                module_params = module_def.get("params", {})
                
                # 加载模块实例
                module = self.module_loader.load_module(module_name, module_params)
                if module:
                    executor.register_module(module)
                    logger.info(f"模块已注册：{module_id} ({module_name})")
                else:
                    logger.error(f"模块加载失败：{module_name}")
            
            # 添加端口连接
            connections_def = flow_definition.get("connections", [])
            for conn_def in connections_def:
                from_port = conn_def["from"]
                to_port = conn_def["to"]
                executor.add_connection(from_port, to_port)
            
            # 执行流程
            outputs = await executor.execute(inputs)
            logger.info(f"流程执行完成：{flow_id}, 输出：{list(outputs.keys())}")
            
            return {
                "success": True,
                "flow_id": flow_id,
                "outputs": outputs,
                "message": "流程执行成功"
            }
            
        except Exception as e:
            logger.error(f"流程执行失败：{flow_id}, 错误：{e}", exc_info=True)
            return {
                "success": False,
                "flow_id": flow_id,
                "outputs": {},
                "message": f"流程执行失败：{str(e)}",
                "error": str(e)
            }


# 全局服务实例
_flow_service: Optional[FlowExecutionService] = None

def get_flow_service(workflow_root: Optional[str] = None) -> FlowExecutionService:
    """获取全局流程执行服务"""
    global _flow_service
    if _flow_service is None:
        _flow_service = FlowExecutionService(workflow_root)
    return _flow_service
