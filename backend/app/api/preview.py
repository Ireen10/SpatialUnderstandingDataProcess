"""
数据预览 API - 通用卡片式可视化
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.services.preview import preview_service

router = APIRouter(prefix="/preview", tags=["preview"])


@router.get("/datasets/{dataset_id}")
async def preview_dataset(
    dataset_id: int,
    page: int = Query(1, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    预览数据集（卡片式展示）
    
    自动识别图片字段，提取图片/视频封面，返回分页数据
    """
    # 验证数据集权限
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在或无权访问")
    
    # 查找数据文件
    if not dataset.storage_path:
        raise HTTPException(status_code=400, detail="数据集未关联数据文件")
    
    data_path = Path(dataset.storage_path)
    if not data_path.exists():
        raise HTTPException(status_code=404, detail="数据文件不存在")
    
    try:
        # 加载并处理数据
        preview_data = await preview_service.load_dataset(
            str(data_path),
            page=page
        )
        
        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            **preview_data
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败：{str(e)}")


@router.get("/files/{file_id}/card")
async def get_file_card(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取单个文件的卡片数据（用于详情展示）
    """
    # TODO: 实现单个文件的卡片数据获取
    return {"file_id": file_id, "message": "TODO"}
