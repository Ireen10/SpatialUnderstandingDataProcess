"""
Initialization and configuration management
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings


class InitService:
    """Service for initialization and configuration management."""
    
    def __init__(self):
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
        self.config_path = self.storage_path / "system" / "init_config.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def is_initialized(self) -> bool:
        """Check if system has been initialized."""
        if not self.config_path.exists():
            return False
        
        try:
            config = self._load_config()
            # Check required fields
            return bool(config.get("data_path")) and bool(config.get("admin_created"))
        except:
            return False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load initialization config."""
        if not self.config_path.exists():
            return {}
        
        return json.loads(self.config_path.read_text())
    
    def _save_config(self, config: Dict[str, Any]):
        """Save initialization config."""
        config["updated_at"] = datetime.utcnow().isoformat()
        self.config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    
    def get_init_status(self) -> Dict[str, Any]:
        """Get initialization status and missing requirements."""
        config = self._load_config()
        
        status = {
            "initialized": self.is_initialized(),
            "data_path_configured": bool(config.get("data_path")),
            "admin_created": bool(config.get("admin_created")),
            "api_configured": bool(config.get("api_key")),
            "storage_backend": config.get("storage_backend", "local"),
            "proxy_configured": bool(config.get("http_proxy") or config.get("https_proxy")),
            "missing_requirements": [],
        }
        
        # Check missing requirements
        if not config.get("data_path"):
            status["missing_requirements"].append("data_path")
        
        if not config.get("admin_created"):
            status["missing_requirements"].append("admin_account")
        
        # Current config values
        status["current_config"] = {
            "data_path": config.get("data_path"),
            "api_base_url": config.get("api_base_url"),
            "api_key_configured": bool(config.get("api_key")),
            "api_model": config.get("api_model"),
            "http_proxy": config.get("http_proxy"),
            "https_proxy": config.get("https_proxy"),
            "storage_backend": config.get("storage_backend", "local"),
            "s3_endpoint": config.get("s3_endpoint"),
            "s3_bucket": config.get("s3_bucket"),
        }
        
        return status
    
    def initialize(
        self,
        data_path: str,
        admin_username: str,
        admin_email: str,
        admin_password: str,
        api_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_model: Optional[str] = None,
        http_proxy: Optional[str] = None,
        https_proxy: Optional[str] = None,
        storage_backend: str = "local",
        s3_endpoint: Optional[str] = None,
        s3_access_key: Optional[str] = None,
        s3_secret_key: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        db_session = None,
    ) -> Dict[str, Any]:
        """
        Initialize system with required configuration.
        
        Args:
            data_path: Path for data storage (required)
            admin_username: Admin username (required)
            admin_email: Admin email (required)
            admin_password: Admin password (required)
            api_base_url: LLM API base URL (optional)
            api_key: LLM API key (optional)
            api_model: LLM model name (optional)
            http_proxy: HTTP proxy URL (optional)
            https_proxy: HTTPS proxy URL (optional)
            storage_backend: Storage backend type (local/s3)
            s3_endpoint: S3 endpoint URL (for S3 backend)
            s3_access_key: S3 access key (for S3 backend)
            s3_secret_key: S3 secret key (for S3 backend)
            s3_bucket: S3 bucket name (for S3 backend)
        
        Returns:
            Initialization result
        """
        # Validate data path
        data_dir = Path(data_path)
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            # Test write permission
            test_file = data_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            raise ValueError(f"Cannot use data path '{data_path}': {e}")
        
        # Build config
        config = {
            "data_path": str(data_dir.absolute()),
            "admin_created": True,
            "admin_username": admin_username,
            "admin_email": admin_email,
            "initialized_at": datetime.utcnow().isoformat(),
            "api_base_url": api_base_url,
            "api_key": api_key,  # Should be encrypted in production
            "api_model": api_model,
            "http_proxy": http_proxy,
            "https_proxy": https_proxy,
            "storage_backend": storage_backend,
            "s3_endpoint": s3_endpoint,
            "s3_access_key": s3_access_key,
            "s3_secret_key": s3_secret_key,
            "s3_bucket": s3_bucket,
        }
        
        self._save_config(config)
        
        # Update settings if needed
        # This would update the running config
        if api_key:
            settings.OPENROUTER_API_KEY = api_key
        if api_base_url:
            settings.OPENROUTER_BASE_URL = api_base_url
        if api_model:
            settings.OPENROUTER_MODEL = api_model
        if data_path:
            settings.DATA_STORAGE_PATH = str(data_dir.absolute())
        if http_proxy:
            settings.HTTP_PROXY = http_proxy
        if https_proxy:
            settings.HTTPS_PROXY = https_proxy
        
        return {
            "success": True,
            "message": "System initialized successfully",
            "data_path": str(data_dir.absolute()),
            "admin_created": True,
        }
    
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update configuration values.
        
        Args:
            updates: Dictionary of config values to update
        
        Returns:
            Updated config
        """
        config = self._load_config()
        
        # Sensitive fields that should not be returned
        sensitive_fields = ["api_key", "s3_secret_key", "s3_access_key"]
        
        for key, value in updates.items():
            if value is not None:
                config[key] = value
        
        self._save_config(config)
        
        # Return config without sensitive fields
        return_config = {k: v for k, v in config.items() if k not in sensitive_fields}
        
        return {
            "success": True,
            "config": return_config,
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration (without sensitive fields)."""
        config = self._load_config()
        
        # Remove sensitive fields
        sensitive_fields = ["api_key", "s3_secret_key", "s3_access_key"]
        return {k: v for k, v in config.items() if k not in sensitive_fields}


# Singleton
init_service = InitService()