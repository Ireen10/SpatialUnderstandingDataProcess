"""
Data conversion service
"""

import json
import os
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import asyncio

from app.core.config import settings
from app.models.dataset import Dataset, DataFile, DataType
from app.models.task import Task, TaskStatus


class ConversionService:
    """Service for converting data between formats."""
    
    def __init__(self):
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
    
    # Common conversion mappings
    FORMAT_MAPPINGS = {
        # Image annotation formats
        "coco_to_yolo": "coco_yolo",
        "yolo_to_coco": "yolo_coco",
        "voc_to_coco": "voc_coco",
        "coco_to_voc": "coco_voc",
        # Text/JSON formats
        "json_to_jsonl": "json_jsonl",
        "jsonl_to_json": "jsonl_json",
        "json_to_csv": "json_csv",
        "csv_to_json": "csv_json",
    }
    
    async def convert_dataset(
        self,
        dataset: Dataset,
        target_format: str,
        output_path: Optional[Path] = None,
        task: Optional[Task] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Convert dataset to target format.
        
        Args:
            dataset: Dataset to convert
            target_format: Target format name
            output_path: Optional output directory
            task: Optional task for progress tracking
            options: Conversion options
        
        Returns:
            Path to converted data
        """
        source_path = self.storage_path / dataset.storage_path
        
        if not output_path:
            output_path = source_path.parent / f"{dataset.name}_converted_{target_format}"
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        if task:
            task.status = TaskStatus.RUNNING.value
            task.started_at = datetime.utcnow()
            task.progress = 0
        
        try:
            # Determine conversion type based on dataset content
            files = self._scan_files(source_path)
            
            if task:
                task.progress = 10
            
            # Run conversion
            converted_count = 0
            total_files = len(files)
            
            for i, file_path in enumerate(files):
                await self._convert_file(file_path, output_path, target_format, options)
                converted_count += 1
                
                if task and total_files > 0:
                    task.progress = 10 + int((converted_count / total_files) * 80)
            
            if task:
                task.status = TaskStatus.COMPLETED.value
                task.progress = 100
                task.completed_at = datetime.utcnow()
                task.output_result = {
                    "output_path": str(output_path),
                    "files_converted": converted_count,
                    "target_format": target_format,
                }
            
            return output_path
            
        except Exception as e:
            if task:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
            raise
    
    async def _convert_file(
        self,
        source_file: Path,
        output_dir: Path,
        target_format: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        """Convert a single file to target format."""
        
        ext = source_file.suffix.lower()
        
        # JSON to JSONL
        if ext == '.json' and target_format == 'jsonl':
            return await self._json_to_jsonl(source_file, output_dir)
        
        # JSONL to JSON
        if ext == '.jsonl' and target_format == 'json':
            return await self._jsonl_to_json(source_file, output_dir)
        
        # JSON to CSV
        if ext == '.json' and target_format == 'csv':
            return await self._json_to_csv(source_file, output_dir)
        
        # Copy other files as-is
        if source_file.is_file():
            dest = output_dir / source_file.name
            shutil.copy2(source_file, dest)
            return dest
        
        return None
    
    async def _json_to_jsonl(self, source: Path, output_dir: Path) -> Path:
        """Convert JSON array to JSONL format."""
        with open(source, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            data = [data]
        
        output_file = output_dir / (source.stem + '.jsonl')
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        return output_file
    
    async def _jsonl_to_json(self, source: Path, output_dir: Path) -> Path:
        """Convert JSONL to JSON array format."""
        items = []
        with open(source, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        
        output_file = output_dir / (source.stem + '.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        
        return output_file
    
    async def _json_to_csv(self, source: Path, output_dir: Path) -> Path:
        """Convert JSON to CSV format."""
        import csv
        
        with open(source, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            data = [data]
        
        if not data:
            return output_dir / (source.stem + '.csv')
        
        # Get all unique keys
        keys = set()
        for item in data:
            if isinstance(item, dict):
                keys.update(item.keys())
        keys = sorted(keys)
        
        output_file = output_dir / (source.stem + '.csv')
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for item in data:
                if isinstance(item, dict):
                    writer.writerow(item)
        
        return output_file
    
    def _scan_files(self, path: Path) -> List[Path]:
        """Scan directory for files."""
        files = []
        for f in path.rglob('*'):
            if f.is_file() and not f.name.startswith('.'):
                files.append(f)
        return files
    
    async def convert_annotations(
        self,
        source_format: str,
        target_format: str,
        annotations_file: Path,
        output_dir: Path,
        images_dir: Optional[Path] = None,
        classes: Optional[List[str]] = None,
    ) -> Path:
        """
        Convert annotation files between formats.
        
        Supported: COCO, YOLO, VOC
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # COCO to YOLO
        if source_format.lower() == 'coco' and target_format.lower() == 'yolo':
            return await self._coco_to_yolo(annotations_file, output_dir, images_dir, classes)
        
        # YOLO to COCO
        if source_format.lower() == 'yolo' and target_format.lower() == 'coco':
            return await self._yolo_to_coco(annotations_file, output_dir, classes)
        
        raise ValueError(f"Unsupported conversion: {source_format} -> {target_format}")
    
    async def _coco_to_yolo(
        self,
        coco_file: Path,
        output_dir: Path,
        images_dir: Optional[Path],
        classes: Optional[List[str]],
    ) -> Path:
        """Convert COCO format annotations to YOLO format."""
        with open(coco_file, 'r', encoding='utf-8') as f:
            coco_data = json.load(f)
        
        # Build category mapping
        categories = {cat['id']: cat['name'] for cat in coco_data.get('categories', [])}
        
        # Use provided classes or extract from COCO
        if not classes:
            classes = [categories[i] for i in sorted(categories.keys())]
        
        # Write classes file
        labels_dir = output_dir / 'labels'
        labels_dir.mkdir(exist_ok=True)
        
        (output_dir / 'classes.txt').write_text('\n'.join(classes) + '\n')
        
        # Group annotations by image
        image_annotations = {}
        for ann in coco_data.get('annotations', []):
            img_id = ann['image_id']
            if img_id not in image_annotations:
                image_annotations[img_id] = []
            image_annotations[img_id].append(ann)
        
        # Convert annotations
        images_info = {img['id']: img for img in coco_data.get('images', [])}
        
        for img_id, anns in image_annotations.items():
            img_info = images_info.get(img_id, {})
            img_w = img_info.get('width', 1)
            img_h = img_info.get('height', 1)
            
            yolo_lines = []
            for ann in anns:
                cat_id = ann['category_id']
                if cat_id not in categories:
                    continue
                
                class_idx = classes.index(categories[cat_id]) if categories[cat_id] in classes else 0
                
                # COCO bbox: [x, y, width, height]
                bbox = ann.get('bbox', [0, 0, 1, 1])
                x, y, w, h = bbox
                
                # Convert to YOLO format (normalized center x, center y, width, height)
                x_center = (x + w / 2) / img_w
                y_center = (y + h / 2) / img_h
                w_norm = w / img_w
                h_norm = h / img_h
                
                yolo_lines.append(f"{class_idx} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")
            
            # Write YOLO annotation file
            img_filename = img_info.get('file_name', f'{img_id}')
            label_filename = Path(img_filename).stem + '.txt'
            (labels_dir / label_filename).write_text('\n'.join(yolo_lines) + '\n')
        
        return labels_dir
    
    async def _yolo_to_coco(
        self,
        yolo_dir: Path,
        output_dir: Path,
        classes: Optional[List[str]],
    ) -> Path:
        """Convert YOLO format annotations to COCO format."""
        # Read classes
        classes_file = yolo_dir / 'classes.txt' if yolo_dir.is_file() else yolo_dir.parent / 'classes.txt'
        
        if classes_file.exists():
            classes = classes_file.read_text().strip().split('\n')
        elif not classes:
            classes = ['object']
        
        # Build COCO structure
        coco_data = {
            "images": [],
            "annotations": [],
            "categories": [
                {"id": i, "name": name, "supercategory": "object"}
                for i, name in enumerate(classes)
            ]
        }
        
        annotation_id = 1
        
        # Find label files
        labels_dir = yolo_dir if yolo_dir.is_dir() else yolo_dir.parent / 'labels'
        label_files = list(labels_dir.glob('*.txt'))
        label_files = [f for f in label_files if f.name != 'classes.txt']
        
        for img_id, label_file in enumerate(label_files, 1):
            # Assume image dimensions (would need actual image or dimensions file)
            img_w, img_h = 640, 640
            
            coco_data['images'].append({
                "id": img_id,
                "file_name": label_file.stem + '.jpg',
                "width": img_w,
                "height": img_h,
            })
            
            # Parse YOLO annotations
            content = label_file.read_text().strip()
            if not content:
                continue
            
            for line in content.split('\n'):
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    x_center = float(parts[1]) * img_w
                    y_center = float(parts[2]) * img_h
                    w = float(parts[3]) * img_w
                    h = float(parts[4]) * img_h
                    
                    # Convert to COCO bbox [x, y, width, height]
                    x = x_center - w / 2
                    y = y_center - h / 2
                    
                    coco_data['annotations'].append({
                        "id": annotation_id,
                        "image_id": img_id,
                        "category_id": class_id,
                        "bbox": [x, y, w, h],
                        "area": w * h,
                        "iscrowd": 0,
                    })
                    annotation_id += 1
        
        # Write COCO JSON
        output_file = output_dir / 'annotations.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(coco_data, f, indent=2)
        
        return output_file


# Singleton
conversion_service = ConversionService()
