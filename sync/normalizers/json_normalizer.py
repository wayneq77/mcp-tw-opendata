from .base import BaseNormalizer
from typing import Dict, List, Any
import json

class JSONNormalizer(BaseNormalizer):
    """JSON 檔案正規化"""
    
    def can_handle(self, content: bytes, content_type: str) -> bool:
        return content_type in ['application/json', '.json'] or self._looks_like_json(content)
    
    def _looks_like_json(self, content: bytes) -> bool:
        try:
            text = content.decode('utf-8', errors='ignore').strip()
            if text.startswith('{') or text.startswith('['):
                json.loads(text)
                return True
        except:
            pass
        return False
    
    def normalize(self, content: bytes, source_info: Dict) -> List[Dict]:
        text = content.decode('utf-8', errors='replace')
        data = json.loads(text)
        
        # 處理不同的 JSON 結構
        if isinstance(data, list):
            return [self._clean_record(item) for item in data if isinstance(item, dict)]
        elif isinstance(data, dict):
            # 常見的 wrapper 結構
            for key in ['data', 'records', 'result', 'items', 'datas']:
                if key in data and isinstance(data[key], list):
                    return [self._clean_record(item) for item in data[key] if isinstance(item, dict)]
            
            # 單一物件
            return [self._clean_record(data)]
        
        return []