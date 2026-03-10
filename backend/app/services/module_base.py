"""模块基类 - v3.0"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ModuleBase(ABC):
    MODULE_ID = "base_module"
    DISPLAY_NAME = "基础模块"
    DESCRIPTION = "模块基类"
    VERSION = "1.0.0"
    INPUTS: List[Dict] = []
    OUTPUTS: List[Dict] = []
    PARAMETERS: List[Dict] = []
    
    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any], params: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行模块"""
        pass
