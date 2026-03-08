"""
SpatialUnderstandingDataProcess - 多模态 VLM 训练数据处理平台
"""

from fastapi import FastAPI
from loguru import logger
import sys

from .core.config import settings
from .api import router as api_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="空间理解多模态 VLM 训练数据处理平台",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    )
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    
    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting up {settings.PROJECT_NAME}")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"Storage path: {settings.DATA_STORAGE_PATH}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down")
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app


app = create_app()
