"""API module"""
from .auth import router as auth_router
from .api_keys import router as api_keys_router
from .datasets import router as datasets_router
from .tasks import router as tasks_router
from .ai import router as ai_router
from .files import router as files_router
from .statistics import router as statistics_router
from .search import router as search_router
from .tools import router as tools_router
from .backups import router as backups_router
from .bugs import router as bugs_router
from .monitoring import router as monitoring_router
from .versions import router as versions_router
from .transform import router as transform_router
from .init import router as init_router
from .deps import get_current_user, get_admin_user, check_initialized, allow_if_not_initialized

__all__ = [
    "auth_router", "api_keys_router", "datasets_router", "tasks_router",
    "ai_router", "files_router", "statistics_router", "search_router",
    "tools_router", "backups_router", "bugs_router", "monitoring_router",
    "versions_router", "transform_router", "init_router",
    "get_current_user", "get_admin_user", "check_initialized", "allow_if_not_initialized",
]