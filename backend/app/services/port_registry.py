"""端口注册表"""
from typing import Dict, List, Optional
from app.services.port import Port, generate_port_id

class PortRegistry:
    def __init__(self):
        self.ports: Dict[str, Port] = {}
    
    def register_port(self, port: Port):
        self.ports[port.port_id] = port
    
    def get_port(self, port_id: str) -> Optional[Port]:
        return self.ports.get(port_id)
    
    def connect(self, from_port_id: str, to_port_id: str) -> bool:
        from_port = self.get_port(from_port_id)
        to_port = self.get_port(to_port_id)
        if from_port and to_port:
            return True
        return False
