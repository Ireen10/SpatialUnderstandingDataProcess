"""
Database session and connection management
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sync_sessionmaker
from sqlalchemy import create_engine
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio

from app.core.config import settings
from app.models.base import Base


# Async engine for async operations
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.LOG_LEVEL == "DEBUG",
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await async_engine.dispose()


# Sync engine for Celery tasks
def get_sync_engine():
    """Get sync engine for Celery and other sync operations."""
    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
    return create_engine(sync_url, echo=settings.LOG_LEVEL == "DEBUG")


def get_sync_session():
    """Get sync session factory for Celery tasks."""
    engine = get_sync_engine()
    return sync_sessionmaker(bind=engine, expire_on_commit=False)
