"""模块加载服务 - v3.0"""
import os
import sys
import importlib.util
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ModuleLoaderService:
    """模块加载服务"""
    
    def __init__(self, modules_root: str):
        """
        初始化模块加载器
        
        Args:
            modules_root: 模块根目录
        """
        self.modules_root = Path(modules_root)
        self.modules_root.mkdir(parents=True, exist_ok=True)
        self.loaded_modules: Dict[str, Any] = {}
        logger.info(f"模块加载服务已初始化：{self.modules_root}")
    
    def load_module(self, module_name: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """
        加载模块
        
        Args:
            module_name: 模块名称（文件夹名）
            params: 模块参数
        
        Returns:
            模块实例，如果加载失败返回 None
        """
        try:
            # 检查是否已加载
            if module_name in self.loaded_modules:
                logger.debug(f"使用缓存的模块：{module_name}")
                module_class = self.loaded_modules[module_name]
            else:
                # 查找模块目录
                module_dir = self.modules_root / module_name
                if not module_dir.exists():
                    # 尝试在模板目录中查找
                    for template_dir in self.modules_root.parent.iterdir():
                        if template_dir.is_dir():
                            modules_subdir = template_dir / "modules"
                            if modules_subdir.exists():
                                module_dir = modules_subdir / module_name
                                if module_dir.exists():
                                    break
                
                if not module_dir.exists():
                    logger.error(f"模块目录不存在：{module_name}")
                    return None
                
                # 加载模块
                module_file = module_dir / "module.py"
                if not module_file.exists():
                    logger.error(f"模块文件不存在：{module_file}")
                    return None
                
                # 动态导入
                spec = importlib.util.spec_from_file_location(
                    f"modules.{module_name}",
                    module_file
                )
                
                if spec is None or spec.loader is None:
                    logger.error(f"无法加载模块：{module_name}")
                    return None
                
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"modules.{module_name}"] = module
                spec.loader.exec_module(module)
                
                # 缓存模块类
                if hasattr(module, '__class__'):
                    self.loaded_modules[module_name] = module.__class__
                else:
                    # 如果模块本身就是可执行的
                    self.loaded_modules[module_name] = module
                    logger.info(f"模块已加载（直接执行）: {module_name}")
                    return module
            
            # 创建模块实例
            module_instance = module_class(params=params)
            logger.info(f"模块已加载：{module_name}")
            return module_instance
            
        except Exception as e:
            logger.error(f"加载模块失败：{module_name}, 错误：{e}", exc_info=True)
            return None
