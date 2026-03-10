"""流程执行器 v3.0 - 完整端口化架构"""
from typing import Dict, Any, List
from collections import defaultdict
from app.services.port import Port, generate_port_id
from app.services.port_registry import PortRegistry
import logging

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    def __init__(self, flow_id: str):
        self.flow_id = flow_id
        self.port_registry = PortRegistry()
        self.modules: Dict[str, Any] = {}
        self.connections: List[Dict] = []
        self.flow_inputs: List[Dict] = []
        self.flow_outputs: List[Dict] = []
    
    def set_flow_ports(self, flow_inputs: List[Dict], flow_outputs: List[Dict]):
        """设置流程输入/输出端口"""
        self.flow_inputs = flow_inputs
        self.flow_outputs = flow_outputs
        
        # 注册流程输入端口
        for idx, port_def in enumerate(flow_inputs):
            port_id = generate_port_id(self.flow_id, port_def.get("port", f"input_{idx}"), idx)
            port = Port(port_id=port_id, owner_id=self.flow_id, port_name=port_def["port"],
                       port_index=idx, is_input=True, port_type=port_def.get("type", "any"))
            self.port_registry.register_port(port)
        
        # 注册流程输出端口
        for idx, port_def in enumerate(flow_outputs):
            port_id = generate_port_id(self.flow_id, port_def.get("port", f"output_{idx}"), idx)
            port = Port(port_id=port_id, owner_id=self.flow_id, port_name=port_def["port"],
                       port_index=idx, is_input=False, port_type=port_def.get("type", "any"))
            self.port_registry.register_port(port)
    
    def register_module(self, module: Any):
        """注册模块"""
        module_id = module.MODULE_ID if hasattr(module, 'MODULE_ID') else module.__class__.__name__
        self.modules[module_id] = module
        
        # 注册模块端口
        if hasattr(module, 'INPUTS'):
            for idx, port_def in enumerate(module.INPUTS):
                port_id = generate_port_id(module_id, port_def.get("port", f"in_{idx}"), idx)
                port = Port(port_id=port_id, owner_id=module_id, port_name=port_def["port"],
                           port_index=idx, is_input=True, port_type=port_def.get("type", "any"))
                self.port_registry.register_port(port)
        
        if hasattr(module, 'OUTPUTS'):
            for idx, port_def in enumerate(module.OUTPUTS):
                port_id = generate_port_id(module_id, port_def.get("port", f"out_{idx}"), idx)
                port = Port(port_id=port_id, owner_id=module_id, port_name=port_def["port"],
                           port_index=idx, is_input=False, port_type=port_def.get("type", "any"))
                self.port_registry.register_port(port)
        
        logger.info(f"模块已注册：{module_id}")
    
    def add_connection(self, from_port_id: str, to_port_id: str):
        """添加端口连接"""
        from_port = self.port_registry.get_port(from_port_id)
        to_port = self.port_registry.get_port(to_port_id)
        
        if not from_port or not to_port:
            logger.warning(f"端口不存在：{from_port_id} 或 {to_port_id}")
            return False
        
        # 检查输入/输出方向
        if from_port.is_input or not to_port.is_input:
            logger.error(f"连接方向错误：{from_port_id} ({'in' if from_port.is_input else 'out'}) → {to_port_id} ({'in' if to_port.is_input else 'out'})")
            return False
        
        self.connections.append({"from": from_port_id, "to": to_port_id})
        logger.info(f"连接已添加：{from_port_id} → {to_port_id}")
        return True
    
    def _topological_sort(self) -> List[str]:
        """拓扑排序确定模块执行顺序"""
        dependencies = defaultdict(set)
        for conn in self.connections:
            from_owner = conn["from"].split(":")[0]
            to_owner = conn["to"].split(":")[0]
            if from_owner != self.flow_id and to_owner != self.flow_id:
                dependencies[to_owner].add(from_owner)
        
        result = []
        all_modules = set(self.modules.keys())
        no_incoming = [m for m in all_modules if not dependencies[m]]
        
        while no_incoming:
            module_id = no_incoming.pop(0)
            result.append(module_id)
            for other in list(dependencies.keys()):
                if module_id in dependencies[other]:
                    dependencies[other].remove(module_id)
                    if not dependencies[other]:
                        no_incoming.append(other)
        
        if len(result) != len(all_modules):
            logger.error(f"检测到循环依赖：{all_modules - set(result)}")
            return list(all_modules)
        
        return result
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行流程"""
        logger.info(f"开始执行流程：{self.flow_id}")
        
        # 注入流程输入到端口
        for port_name, value in inputs.items():
            for port in self.port_registry.ports.values():
                if port.owner_id == self.flow_id and port.is_input and port.port_name == port_name:
                    port.value = value
                    logger.info(f"输入已注入：{port.port_id} = {value}")
        
        # 拓扑排序获取执行顺序
        execution_order = self._topological_sort()
        logger.info(f"执行顺序：{execution_order}")
        
        # 按顺序执行模块
        for module_id in execution_order:
            module = self.modules.get(module_id)
            if not module:
                logger.error(f"模块不存在：{module_id}")
                continue
            
            logger.info(f"执行模块：{module_id}")
            
            # 收集模块输入（从上游端口）
            module_input = {}
            if hasattr(module, 'INPUTS'):
                for idx, port_def in enumerate(module.INPUTS):
                    port_id = generate_port_id(module_id, port_def.get("port", f"in_{idx}"), idx)
                    # 找到连接到这个输入端口的源
                    for conn in self.connections:
                        if conn["to"] == port_id:
                            source_port = self.port_registry.get_port(conn["from"])
                            if source_port and source_port.value is not None:
                                module_input[port_def["port"]] = source_port.value
                                logger.debug(f"输入端口 {port_def['port']} 从 {conn['from']} 获取值")
            
            # 执行模块
            try:
                if hasattr(module, 'execute'):
                    import asyncio
                    if asyncio.iscoroutinefunction(module.execute):
                        module_output = await module.execute(module_input, getattr(module, 'params', {}))
                    else:
                        module_output = module.execute(module_input, getattr(module, 'params', {}))
                else:
                    logger.error(f"模块 {module_id} 没有 execute 方法")
                    continue
                
                logger.debug(f"模块输出：{module_output}")
                
                # 保存模块输出到端口
                if hasattr(module, 'OUTPUTS'):
                    for idx, port_def in enumerate(module.OUTPUTS):
                        port_id = generate_port_id(module_id, port_def.get("port", f"out_{idx}"), idx)
                        port = self.port_registry.get_port(port_id)
                        if port:
                            value = module_output.get(port_def["port"]) if isinstance(module_output, dict) else module_output
                            port.value = value
                            logger.debug(f"输出端口 {port_def['port']} 已保存值")
                
            except Exception as e:
                logger.error(f"模块 {module_id} 执行失败：{e}", exc_info=True)
                raise
        
        # 收集流程输出
        outputs = {}
        for port_def in self.flow_outputs:
            port_name = port_def.get("port", "output")
            for port in self.port_registry.ports.values():
                if port.owner_id == self.flow_id and not port.is_input and port.port_name == port_name:
                    outputs[port_name] = port.value
                    logger.debug(f"流程输出 {port_name} 已收集")
        
        logger.info(f"流程执行完成：{self.flow_id}")
        return outputs
