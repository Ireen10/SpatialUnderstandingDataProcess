"""流程存储服务"""
import json
import os
from pathlib import Path
from datetime import datetime

class FlowStorageService:
    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root)
        self.flows_dir = self.storage_root / "flows"
        self.flows_dir.mkdir(parents=True, exist_ok=True)
    
    def save_flow(self, flow_id: str, flow_def: dict) -> bool:
        flow_file = self.flows_dir / f"{flow_id}.json"
        flow_def["updated_at"] = datetime.now().isoformat()
        with open(flow_file, 'w', encoding='utf-8') as f:
            json.dump(flow_def, f, indent=2, ensure_ascii=False)
        return True
    
    def load_flow(self, flow_id: str):
        flow_file = self.flows_dir / f"{flow_id}.json"
        if flow_file.exists():
            with open(flow_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def list_flows(self):
        flows = []
        for flow_file in self.flows_dir.glob("*.json"):
            flows.append({"flow_id": flow_file.stem})
        return flows
