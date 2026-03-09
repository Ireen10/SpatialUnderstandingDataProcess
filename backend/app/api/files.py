"""
文本文件预览 API
支持 md/txt/json/jsonl 等文本格式预览
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset, DataFile

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{file_id}/preview")
async def preview_file(
    file_id: int,
    max_lines: int = Query(100, ge=1, le=1000, description="最大行数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    预览文本文件内容
    
    支持格式：txt, md, json, jsonl, csv, tsv
    """
    # 验证文件权限
    result = await db.execute(
        select(DataFile).where(
            DataFile.id == file_id,
            DataFile.dataset_id.in_(
                select(Dataset.id).where(Dataset.user_id == current_user.id)
            )
        )
    )
    data_file = result.scalar_one_or_none()
    if not data_file:
        raise HTTPException(status_code=404, detail="文件不存在或无权访问")
    
    # 检查文件类型
    text_extensions = {'.txt', '.md', '.json', '.jsonl', '.csv', '.tsv', '.xml', '.html'}
    file_ext = Path(data_file.filename).suffix.lower()
    
    if file_ext not in text_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持预览的文件格式：{file_ext}",
        )
    
    # 构建文件路径
    if not data_file.relative_path:
        raise HTTPException(status_code=400, detail="文件路径信息缺失")
    
    # 从 dataset 获取存储路径
    dataset_result = await db.execute(
        select(Dataset).where(Dataset.id == data_file.dataset_id)
    )
    dataset = dataset_result.scalar_one()
    
    file_path = Path(dataset.storage_path) / data_file.relative_path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="物理文件不存在")
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"\n... (仅显示前 {max_lines} 行，共 {data_file.file_size} 字节)")
                    break
                lines.append(line)
            
            content = ''.join(lines)
        
        return {
            "file_id": file_id,
            "filename": data_file.filename,
            "file_type": data_file.file_type,
            "file_size": data_file.file_size,
            "lines_displayed": len(lines),
            "truncated": len(lines) >= max_lines,
            "content": content,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败：{str(e)}")


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取文件完整内容（用于下载或大文件）
    """
    # 权限验证（同上）
    result = await db.execute(
        select(DataFile).where(
            DataFile.id == file_id,
            DataFile.dataset_id.in_(
                select(Dataset.id).where(Dataset.user_id == current_user.id)
            )
        )
    )
    data_file = result.scalar_one_or_none()
    if not data_file:
        raise HTTPException(status_code=404, detail="文件不存在或无权访问")
    
    # 构建路径
    dataset_result = await db.execute(
        select(Dataset).where(Dataset.id == data_file.dataset_id)
    )
    dataset = dataset_result.scalar_one()
    
    file_path = Path(dataset.storage_path) / data_file.relative_path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="物理文件不存在")
    
    # 返回文件
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(file_path),
        filename=data_file.filename,
        media_type=data_file.file_type,
    )
