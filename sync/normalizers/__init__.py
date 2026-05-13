from typing import List, Dict
from .base import BaseNormalizer
from .csv_normalizer import CSVNormalizer
from .json_normalizer import JSONNormalizer
from .xml_normalizer import XMLNormalizer
from .pdf_normalizer import PDFNormalizer
from .geojson_normalizer import GeoJSONNormalizer

# 所有 normalizer 的工廠
NORMALIZERS = [
    GeoJSONNormalizer(),
    JSONNormalizer(),
    CSVNormalizer(),
    XMLNormalizer(),
    PDFNormalizer(),
]

def normalize(content: bytes, content_type: str, source_info: Dict) -> List[Dict]:
    """
    根據檔案類型自動選擇適合的 normalizer
    
    Args:
        content: 原始檔案內容
        content_type: MIME type 或副檔名
        source_info: 來源資訊
        
    Returns:
        正規化後的 records list
    """
    for normalizer in NORMALIZERS:
        if normalizer.can_handle(content, content_type):
            try:
                return normalizer.normalize(content, source_info)
            except Exception as e:
                return [{"error": str(e), "normalizer": normalizer.__class__.__name__}]
    
    # 找不到適合的 normalizer
    return [{"error": "unsupported format", "content_type": content_type}]