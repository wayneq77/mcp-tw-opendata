"""
Base normalizer class - 所有 normalizer 的基底
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseNormalizer(ABC):
    """正規化的基底類別"""
    
    @abstractmethod
    def normalize(self, content: bytes, source_info: Dict) -> List[Dict]:
        """
        將原始檔案內容正規化為統一的 JSON 格式
        
        Args:
            content: 原始檔案內容（bytes）
            source_info: 來源資訊（URL, filename 等）
            
        Returns:
            List of normalized records (each record is a dict)
        """
        pass
    
    @abstractmethod
    def can_handle(self, content: bytes, content_type: str) -> bool:
        """
        判斷這個 normalizer 是否能處理這個檔案
        
        Args:
            content: 檔案內容
            content_type: MIME type 或副檔名
            
        Returns:
            True if this normalizer can handle the content
        """
        pass
    
    def _clean_value(self, value: Any) -> Any:
        """清理單一值"""
        if value is None:
            return ""
        
        if isinstance(value, (int, float, bool)):
            return value
        
        if isinstance(value, str):
            # 移除前後空白
            value = value.strip()
            
            # 處理全形數字（可選）
            # 如果有需要可以在这里转换全形到半形
            
            # 如果是空的而且是數字相關的，返回空字串
            if value == "":
                return ""
            
            return value
        
        # 其他類型轉為字串
        return str(value)
    
    def _clean_record(self, record: Dict) -> Dict:
        """清理一筆記錄"""
        cleaned = {}
        for key, value in record.items():
            # 處理鍵名（可能有特殊字元）
            clean_key = key.strip()
            
            # 處理值
            if isinstance(value, dict):
                cleaned[clean_key] = self._clean_record(value)
            elif isinstance(value, list):
                cleaned[clean_key] = [self._clean_value(v) for v in value]
            else:
                cleaned[clean_key] = self._clean_value(value)
        
        return cleaned