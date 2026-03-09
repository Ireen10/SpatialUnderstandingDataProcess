"""
数据预览服务 - 通用卡片式可视化
提取数据集中的图片和视频，生成卡片式展示所需的数据
"""

import json
import base64
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import cv2
import pandas as pd
import aiohttp
from PIL import Image
import io


class PreviewService:
    """数据预览服务 - 支持 parquet/CSV/JSON 等格式"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.max_pages = 30
        self.page_size = 50
        
    async def load_dataset(
        self,
        file_path: str,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        加载数据集并分页
        
        Args:
            file_path: 数据文件路径（parquet/csv/json）
            page: 页码（1-based）
            
        Returns:
            {
                "total": 总条数,
                "page": 当前页,
                "page_size": 每页数量,
                "total_pages": 总页数,
                "data": 当前页数据列表,
                "image_field": 识别到的图片字段名,
                "has_video": 是否包含视频字段
            }
        """
        try:
            # 根据文件类型加载数据
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在：{file_path}")
            
            # 使用 asyncio 运行同步的 pandas 操作
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                self.executor,
                self._load_dataframe,
                str(file_path)
            )
            
            # 识别图片字段
            image_field = self._find_image_field(df)
            has_video = self._has_video_field(df)
            
            # 分页
            total = len(df)
            total_pages = min((total + self.page_size - 1) // self.page_size, self.max_pages)
            page = min(page, total_pages)
            
            start_idx = (page - 1) * self.page_size
            end_idx = min(start_idx + self.page_size, total)
            page_df = df.iloc[start_idx:end_idx]
            
            # 转换为字典列表
            data = page_df.to_dict(orient='records')
            
            # 提取图片/视频信息
            processed_data = await self._process_data(data, image_field, file_path.parent)
            
            return {
                "total": total,
                "page": page,
                "page_size": self.page_size,
                "total_pages": total_pages,
                "data": processed_data,
                "image_field": image_field,
                "has_video": has_video,
                "fields": list(df.columns),
            }
            
        except Exception as e:
            raise Exception(f"加载数据集失败：{str(e)}")
    
    def _load_dataframe(self, file_path: str) -> pd.DataFrame:
        """加载 DataFrame（同步方法）"""
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        if ext == '.parquet':
            return pd.read_parquet(file_path, engine='pyarrow')
        elif ext == '.tsv':
            return pd.read_csv(file_path, sep='\t', low_memory=False)
        elif ext == '.csv':
            return pd.read_csv(file_path, low_memory=False)
        elif ext in ['.json', '.jsonl']:
            return pd.read_json(file_path, lines=True)
        else:
            raise ValueError(f"不支持的文件格式：{ext}")
    
    def _find_image_field(self, df: pd.DataFrame) -> Optional[str]:
        """查找图片字段（大小写不敏感）"""
        image_keywords = ['image', 'img', 'picture', 'photo']
        columns_lower = {col.lower(): col for col in df.columns}
        
        for keyword in image_keywords:
            for col_lower, col_orig in columns_lower.items():
                if keyword in col_lower:
                    return col_orig
        
        return None
    
    def _has_video_field(self, df: pd.DataFrame) -> bool:
        """检查是否有视频字段"""
        video_keywords = ['video', 'vid', 'movie', 'clip']
        columns_lower = [col.lower() for col in df.columns]
        
        return any(keyword in col for col in columns_lower for keyword in video_keywords)
    
    async def _process_data(
        self,
        data: List[Dict[str, Any]],
        image_field: Optional[str],
        dataset_dir: Path
    ) -> List[Dict[str, Any]]:
        """处理数据，提取图片/视频信息"""
        if not image_field:
            return data
        
        # 并发处理所有记录
        tasks = [
            self._process_record(record, image_field, dataset_dir)
            for record in data
        ]
        return await asyncio.gather(*tasks)
    
    async def _process_record(
        self,
        record: Dict[str, Any],
        image_field: Optional[str],
        dataset_dir: Path
    ) -> Dict[str, Any]:
        """处理单条记录"""
        result = record.copy()
        
        # 处理图片字段
        if image_field and image_field in record:
            images = await self._extract_images(record[image_field], dataset_dir)
            result['_images'] = images
        
        # 处理视频字段（提取封面）
        video_field = self._find_video_field(record)
        if video_field and video_field in record:
            cover = await self._extract_video_cover(record[video_field], dataset_dir)
            result['_video_cover'] = cover
        
        return result
    
    async def _extract_images(
        self,
        image_data: Any,
        dataset_dir: Path
    ) -> List[Dict[str, str]]:
        """
        提取图片，返回本地路径列表
        
        支持：
        - URL: 下载到 images/ 目录
        - Base64: 解码保存到 images/ 目录
        - 路径：直接使用
        """
        images_dir = dataset_dir / 'images'
        images_dir.mkdir(exist_ok=True)
        
        # 处理单个图片或多图片列表
        if isinstance(image_data, str):
            image_list = [image_data]
        elif isinstance(image_data, list):
            image_list = image_data
        else:
            return []
        
        results = []
        for idx, img in enumerate(image_list):
            if not img:
                continue
                
            if isinstance(img, str):
                # 判断是 URL、Base64 还是路径
                if img.startswith('http://') or img.startswith('https://'):
                    # URL - 下载
                    local_path = await self._download_image(img, images_dir, idx)
                    if local_path:
                        results.append({"type": "local", "path": str(local_path)})
                elif img.startswith('data:image') or (len(img) > 100 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in img[:100])):
                    # Base64 - 解码保存
                    local_path = self._save_base64_image(img, images_dir, idx)
                    if local_path:
                        results.append({"type": "local", "path": str(local_path)})
                else:
                    # 路径 - 直接使用
                    results.append({"type": "path", "path": img})
        
        return results
    
    async def _download_image(
        self,
        url: str,
        images_dir: Path,
        idx: int
    ) -> Optional[Path]:
        """下载图片到本地"""
        try:
            filename = f"img_{idx}_{hash(url) % 10000}.jpg"
            local_path = images_dir / filename
            
            if local_path.exists():
                return local_path
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        # 保存到本地
                        local_path.write_bytes(content)
                        return local_path
        except Exception as e:
            print(f"下载图片失败 {url}: {e}")
        
        return None
    
    def _save_base64_image(
        self,
        base64_data: str,
        images_dir: Path,
        idx: int
    ) -> Optional[Path]:
        """保存 Base64 图片到本地"""
        try:
            # 移除 data:image 前缀
            if ',' in base64_data:
                base64_data = base64_data.split(',', 1)[1]
            
            img_data = base64.b64decode(base64_data)
            filename = f"img_{idx}_{hash(base64_data) % 10000}.jpg"
            local_path = images_dir / filename
            
            if not local_path.exists():
                local_path.write_bytes(img_data)
            
            return local_path
        except Exception as e:
            print(f"保存 Base64 图片失败：{e}")
        
        return None
    
    def _find_video_field(self, record: Dict[str, Any]) -> Optional[str]:
        """查找视频字段"""
        video_keywords = ['video', 'vid', 'movie', 'clip']
        for key in record.keys():
            if any(keyword in key.lower() for keyword in video_keywords):
                return key
        return None
    
    async def _extract_video_cover(
        self,
        video_data: Any,
        dataset_dir: Path
    ) -> Optional[Dict[str, str]]:
        """提取视频第一帧作为封面"""
        covers_dir = dataset_dir / 'covers'
        covers_dir.mkdir(exist_ok=True)
        
        # 如果视频数据是路径或 URL
        if isinstance(video_data, str):
            if video_data.startswith(('http://', 'https://')):
                # TODO: 下载视频并提取封面（暂时跳过）
                return {"type": "unsupported", "message": "不支持远程视频封面提取"}
            elif Path(video_data).exists():
                # 本地视频文件
                return self._extract_local_video_cover(Path(video_data), covers_dir)
        
        return None
    
    def _extract_local_video_cover(
        self,
        video_path: Path,
        covers_dir: Path
    ) -> Optional[Dict[str, str]]:
        """提取本地视频第一帧"""
        try:
            filename = f"cover_{hash(str(video_path)) % 10000}.jpg"
            cover_path = covers_dir / filename
            
            if cover_path.exists():
                return {"type": "local", "path": str(cover_path)}
            
            # 使用 OpenCV 提取第一帧
            cap = cv2.VideoCapture(str(video_path))
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                cv2.imwrite(str(cover_path), frame)
                return {"type": "local", "path": str(cover_path)}
        except Exception as e:
            print(f"提取视频封面失败：{e}")
        
        return None


# 单例
preview_service = PreviewService()
