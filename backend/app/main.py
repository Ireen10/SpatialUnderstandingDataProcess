"""
Main FastAPI application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db, close_db
from app.services.init import init_service
from app.api import auth, api_keys, datasets, tasks, ai, files, statistics, search, tools, backups, bugs, monitoring, versions, transform, init, preview


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="空间理解多模态 VLM 训练数据处理平台",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Init routes - always accessible
app.include_router(init.router, prefix=settings.API_V1_PREFIX)

# Check initialization middleware
@app.middleware("http")
async def check_initialization(request: Request, call_next):
    """Check if system is initialized before allowing access to protected endpoints."""
    # Public endpoints that don't require initialization
    public_paths = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        f"{settings.API_V1_PREFIX}/init/",
    ]
    
    # Check if path is public
    is_public = any(request.url.path.startswith(p) for p in public_paths)
    
    if is_public:
        return await call_next(request)
    
    # Check initialization status
    if not init_service.is_initialized():
        return JSONResponse(
            status_code=503,
            content={
                "error": "system_not_initialized",
                "message": "System requires initialization. Please complete setup via /api/v1/init/initialize",
                "status_endpoint": f"{settings.API_V1_PREFIX}/init/status",
            }
        )
    
    return await call_next(request)

# Protected routes - require initialization
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(api_keys.router, prefix=settings.API_V1_PREFIX)
app.include_router(datasets.router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai.router, prefix=settings.API_V1_PREFIX)
app.include_router(files.router, prefix=settings.API_V1_PREFIX)
app.include_router(statistics.router, prefix=settings.API_V1_PREFIX)
app.include_router(search.router, prefix=settings.API_V1_PREFIX)
app.include_router(tools.router, prefix=settings.API_V1_PREFIX)
app.include_router(backups.router, prefix=settings.API_V1_PREFIX)
app.include_router(bugs.router, prefix=settings.API_V1_PREFIX)
app.include_router(monitoring.router, prefix=settings.API_V1_PREFIX)
app.include_router(versions.router, prefix=settings.API_V1_PREFIX)
app.include_router(transform.router, prefix=settings.API_V1_PREFIX)
app.include_router(preview.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
