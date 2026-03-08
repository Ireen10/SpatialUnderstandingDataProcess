"""
Celery worker configuration and tasks
"""

from celery import Celery
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "spatial_data_process",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# Import tasks
celery_app.autodiscover_tasks(["app.tasks"])


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def download_huggingface_task(
    self,
    task_id: int,
    dataset_id: int,
    repo_id: str,
    allow_patterns: Optional[list] = None,
    ignore_patterns: Optional[list] = None,
) -> Dict[str, Any]:
    """Download dataset from HuggingFace Hub."""
    import asyncio
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    from app.core.config import settings
    from app.models.task import Task, TaskStatus
    from app.models.dataset import Dataset
    from app.services.download import download_service
    
    # Sync database session
    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    
    with Session() as db:
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not task or not dataset:
                return {"error": "Task or dataset not found"}
            
            task.status = TaskStatus.RUNNING.value
            task.started_at = datetime.utcnow()
            db.commit()
            
            # Run async download
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    download_service.download_from_huggingface(
                        repo_id=repo_id,
                        dataset=dataset,
                        task=task,
                        allow_patterns=allow_patterns,
                        ignore_patterns=ignore_patterns,
                    )
                )
            finally:
                loop.close()
            
            db.commit()
            return {"status": "completed", "task_id": task_id}
            
        except Exception as e:
            db.rollback()
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e)
            return {"error": str(e)}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def download_url_task(
    self,
    task_id: int,
    dataset_id: int,
    url: str,
) -> Dict[str, Any]:
    """Download file from URL."""
    import asyncio
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    from app.core.config import settings
    from app.models.task import Task, TaskStatus
    from app.models.dataset import Dataset
    from app.services.download import download_service
    
    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    
    with Session() as db:
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not task or not dataset:
                return {"error": "Task or dataset not found"}
            
            task.status = TaskStatus.RUNNING.value
            task.started_at = datetime.utcnow()
            db.commit()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    download_service.download_from_url(url=url, dataset=dataset, task=task)
                )
            finally:
                loop.close()
            
            db.commit()
            return {"status": "completed", "task_id": task_id}
            
        except Exception as e:
            db.rollback()
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e)
            return {"error": str(e)}


@celery_app.task(bind=True)
def extract_metadata_task(self, dataset_id: int) -> Dict[str, Any]:
    """Extract metadata for all files in a dataset."""
    import asyncio
    from pathlib import Path
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    from app.core.config import settings
    from app.models.dataset import DataFile
    from app.services.metadata import metadata_service
    from app.services.download import download_service
    
    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    
    with Session() as db:
        files = db.query(DataFile).filter(DataFile.dataset_id == dataset_id).all()
        count = 0
        
        for file in files:
            file_path = Path(settings.DATA_STORAGE_PATH) / file.relative_path
            if file_path.exists():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    metadata = loop.run_until_complete(
                        metadata_service.extract_metadata(file, file_path)
                    )
                    if metadata:
                        db.add(metadata)
                        count += 1
                finally:
                    loop.close()
        
        db.commit()
        return {"extracted": count}
