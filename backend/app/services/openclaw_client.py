"""OpenClaw Gateway 客户端 - v4.0

支持：
- 功能模块创建
- 分支模块创建
- 模块编辑（版本管理）
- 模块反馈处理
"""
import httpx
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# 模块仓库根目录
MODULES_ROOT = os.environ.get("MODULES_ROOT", "/mnt/d/GithubRepo/SpatialUnderstandingDataProcess/modules")


class PortDefinition(BaseModel):
    """端口定义（无类型约束）"""
    name: str
    description: str = ""


class ParamDefinition(BaseModel):
    """参数定义（无类型约束）"""
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
    edit_description: str  # 用户描述要修改的内容


class ModuleFeedbackRequest(BaseModel):
    """模块反馈请求"""
    module_id: str
    version: int
    error_type: str
    error_message: str
    traceback: str
    user_description: str = ""
    callback_url: str = ""


class OpenClawClient:
    """OpenClaw 客户端"""
    
    def __init__(self, gateway_url: str = None, gateway_token: str = None, agent_id: str = "glm-coder"):
        self.gateway_url = gateway_url or os.environ.get("OPENCLAW_GATEWAY_URL", "http://localhost:18789")
        self.gateway_token = gateway_token or os.environ.get("OPENCLAW_GATEWAY_TOKEN", "")
        self.agent_id = agent_id
        self._session: Optional[httpx.AsyncClient] = None
    
    async def get_session(self) -> httpx.AsyncClient:
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(
                base_url=self.gateway_url,
                headers={"Authorization": f"Bearer {self.gateway_token}", "Content-Type": "application/json"},
                timeout=180.0  # 增加超时时间，AI 生成代码可能需要更长时间
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.is_closed:
            await self._session.aclose()
    
    async def _send_to_agent(self, message: str, mode: str = "run") -> Dict[str, Any]:
        """发送消息到 OpenClaw agent"""
        try:
            session = await self.get_session()
            response = await session.post("/api/session/send", json={
                "agentId": self.agent_id,
                "message": message,
                "mode": mode
            })
            
            if response.status_code == 200:
                return {"success": True, "response": response.json()}
            else:
                return {"success": False, "error": f"Gateway returned {response.status_code}: {response.text}"}
        except Exception as e:
            logger.error(f"发送消息到 OpenClaw 失败：{e}")
            return {"success": False, "error": str(e)}
    
    async def create_function_module(self, request: CreateFunctionModuleRequest) -> Dict[str, Any]:
        """调用 OpenClaw 创建功能模块"""
        
        # 构建提示词
        prompt = f"""请创建一个功能模块：

模块名称：{request.module_name}
功能描述：{request.description}

输入端口：
{self._format_ports(request.inputs)}

输出端口：
{self._format_ports(request.outputs)}

参数：
{self._format_params(request.parameters)}

目标目录：{MODULES_ROOT}

请按照 workflow-module-creator skill 中定义的功能模块规范生成代码。"""

        result = await self._send_to_agent(prompt)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "功能模块创建成功",
                "module_name": request.module_name
            }
        return result
    
    async def create_branch_module(self, request: CreateBranchModuleRequest) -> Dict[str, Any]:
        """调用 OpenClaw 创建分支模块"""
        
        # 格式化条件
        conditions_str = "\n".join([
            f"- {c.id}: {c.description}"
            for c in request.conditions
        ])
        
        prompt = f"""请创建一个分支模块：

模块名称：{request.module_name}
描述：{request.description}

输入数据：
- 名称：{request.input.name}
- 描述：{request.input.description}

条件分支（按优先级顺序）：
{conditions_str}

兜底分支：default（自动添加）

目标目录：{MODULES_ROOT}

请按照 workflow-module-creator skill 中定义的分支模块规范生成代码。
注意：
1. 分支模块不处理数据，只决定数据流向
2. 数据透传（输出 = 输入）
3. 自动记录分支执行日志"""

        result = await self._send_to_agent(prompt)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "分支模块创建成功",
                "module_name": request.module_name
            }
        return result
    
    async def edit_module(self, request: EditModuleRequest) -> Dict[str, Any]:
        """调用 OpenClaw 编辑模块（创建新版本）"""
        
        prompt = f"""请编辑模块：

模块ID：{request.module_id}
当前版本：{request.current_version}

用户修改描述：
{request.edit_description}

请根据用户描述修改模块代码，并创建新版本（v{request.current_version + 1}）。
更新 CHANGELOG.md 记录变更内容。

目标目录：{MODULES_ROOT}/{request.module_id}/"""

        result = await self._send_to_agent(prompt)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"模块已更新到 v{request.current_version + 1}",
                "new_version": request.current_version + 1
            }
        return result
    
    async def submit_feedback(self, request: ModuleFeedbackRequest) -> Dict[str, Any]:
        """提交模块反馈"""
        
        prompt = f"""【模块反馈】
模块ID：{request.module_id}
版本：v{request.version}
路径：{MODULES_ROOT}/{request.module_id}/v{request.version}/
回调地址：{request.callback_url}

错误信息：
  {request.error_type}: {request.error_message}

调用栈：
{request.traceback}

用户描述：{request.user_description}

请分析并修复这个问题，创建新版本并更新 CHANGELOG.md。"""

        result = await self._send_to_agent(prompt)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "反馈已处理"
            }
        return result
    
    def _format_ports(self, ports: List[PortDefinition]) -> str:
        """格式化端口列表"""
        if not ports:
            return "（无）"
        return "\n".join([
            f"- {p.name}: {p.description or '无描述'}"
            for p in ports
        ])
    
    def _format_params(self, params: List[ParamDefinition]) -> str:
        """格式化参数列表"""
        if not params:
            return "（无）"
        return "\n".join([
            f"- {p.name}: 默认值 {p.default}, {p.description or '无描述'}"
            for p in params
        ])


# 全局客户端实例
openclaw_client = OpenClawClient()