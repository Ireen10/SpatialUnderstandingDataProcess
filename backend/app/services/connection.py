"""连接数据类"""
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Connection:
    from_port_id: str
    to_port_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
