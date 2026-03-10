"""
端口（Port）系统 - v3.0 端口化架构
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class Port:
    """端口类"""
    port_id: str
    owner_id: str
    port_name: str
    port_index: int
    is_input: bool
    port_type: str = "any"
    description: str = ""
    value: Optional[Any] = None

    def __str__(self):
        direction = "in" if self.is_input else "out"
        return f"{self.port_id} ({direction}, {self.port_type})"


def generate_port_id(owner_id: str, port_name: str, port_index: int) -> str:
    """生成端口 ID: {owner}:{port}:{index}"""
    return f"{owner_id}:{port_name}:{port_index}"


def parse_port_id(port_id: str) -> dict:
    """解析端口 ID"""
    parts = port_id.split(":")
    if len(parts) != 3:
        raise ValueError(f"端口 ID 格式错误：{port_id}")
    return {
        "owner_id": parts[0],
        "port_name": parts[1],
        "port_index": int(parts[2]),
    }
