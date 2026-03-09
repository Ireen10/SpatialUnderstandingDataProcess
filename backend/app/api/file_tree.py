"""
文件树 API - 返回数据集的目录树结构
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dataset import Dataset, DataFile

router = APIRouter(prefix="/datasets", tags=["datasets"])


class TreeNode:
    """文件树节点"""
    def __init__(self, name: str, is_dir: bool, path: str = "", children: List = None):
        self.name = name
        self.is_dir = is_dir
        self.path = path
        self.children = children or []
        self.file_count = 0
        self.total_size = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "is_dir": self.is_dir,
            "path": self.path,
            "children": [child.to_dict() for child in self.children],
            "file_count": self.file_count,
            "total_size": self.total_size,
        }


@router.get("/{dataset_id}/tree")
async def get_dataset_tree(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取数据集的文件树结构
    """
    # 验证数据集权限
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在或无权访问")
    
    # 获取所有文件
    files_result = await db.execute(
        select(DataFile).where(DataFile.dataset_id == dataset_id).order_by(DataFile.relative_path)
    )
    files = files_result.scalars().all()
    
    # 构建树结构
    root = TreeNode(name=dataset.name, is_dir=True, path="")
    
    for file in files:
        # 跳过 .cache 等目录
        if '.cache' in file.relative_path or file.relative_path.startswith('.'):
            continue
        
        parts = Path(file.relative_path).parts
        current = root
        
        # 创建中间目录
        for i, part in enumerate(parts[:-1]):
            # 查找或创建目录节点
            child = next((c for c in current.children if c.name == part), None)
            if not child:
                child = TreeNode(
                    name=part,
                    is_dir=True,
                    path=str(Path(*parts[:i+1])),
                )
                current.children.append(child)
            current = child
        
        # 添加文件节点
        file_node = TreeNode(
            name=parts[-1],
            is_dir=False,
            path=file.relative_path,
        )
        file_node.file_count = 1
        file_node.total_size = file.file_size
        
        current.children.append(file_node)
        
        # 更新祖先节点的统计
        node = current
        while node != root:
            node.file_count += 1
            node.total_size += file.file_size
            # 找到父节点
            parent_path = str(Path(file.relative_path).parent)
            node = next((c for c in root.children if c.path == parent_path), root)
    
    # 递归计算目录的文件数和大小
    def calc_stats(node: TreeNode):
        if not node.is_dir:
            return node.file_count, node.total_size
        
        total_files = 0
        total_size = 0
        for child in node.children:
            files, size = calc_stats(child)
            total_files += files
            total_size += size
        
        node.file_count = total_files
        node.total_size = total_size
        return total_files, total_size
    
    calc_stats(root)
    
    return {
        "dataset_id": dataset_id,
        "dataset_name": dataset.name,
        "total_files": dataset.total_files,
        "total_size": dataset.total_size,
        "tree": root.to_dict(),
    }
