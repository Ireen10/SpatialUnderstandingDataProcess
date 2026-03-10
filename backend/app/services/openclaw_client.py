"""OpenClaw Gateway 客户端 - v3.0"""
import httpx
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

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
                timeout=120.0
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.is_closed:
            await self._session.aclose()
    
    async def create_module(self, module_name: str, description: str, inputs: list, outputs: list, parameters: list, workflow_root: str) -> Dict[str, Any]:
        """调用 OpenClaw 创建模块"""
        try:
            session = await self.get_session()
            prompt = f"""请创建一个工作流模块：
- 名称：{module_name}
- 描述：{description}
- 输入：{inputs}
- 输出：{outputs}
- 参数：{parameters}

请在以下目录生成模块代码：{workflow_root}/modules/{module_name}/
模块结构要求：__init__.py, module.py, README.md"""
            
            response = await session.post("/api/session/send", json={
                "agentId": self.agent_id,
                "message": prompt,
                "mode": "run"
            })
            
            if response.status_code == 200:
                return {"success": True, "message": "模块创建成功", "module_path": f"{workflow_root}/modules/{module_name}/"}
            else:
                return {"success": False, "error": f"Gateway returned {response.status_code}: {response.text}"}
        except Exception as e:
            logger.error(f"创建模块失败：{e}")
            return {"success": False, "error": str(e)}
    
    async def submit_feedback(self, module_name: str, error_type: str, error_message: str, traceback: str, user_description: str = "", callback_url: str = "") -> Dict[str, Any]:
        """提交模块反馈"""
        try:
            session = await self.get_session()
            prompt = f"""【模块反馈】
模块：{module_name}
错误：{error_type}: {error_message}
调用栈：{traceback}
用户描述：{user_description}
回调地址：{callback_url}

请分析并修复这个问题。"""
            
            response = await session.post("/api/session/send", json={
                "agentId": self.agent_id,
                "message": prompt,
                "mode": "run"
            })
            
            return {"success": response.status_code == 200, "message": "反馈已提交"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# 全局客户端实例
openclaw_client = OpenClawClient()
