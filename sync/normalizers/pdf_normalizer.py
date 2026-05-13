from .base import BaseNormalizer
from typing import Dict, List, Any

class PDFNormalizer(BaseNormalizer):
    """PDF 檔案正規化（文字萃取）"""
    
    def can_handle(self, content: bytes, content_type: str) -> bool:
        return content_type in ['application/pdf', '.pdf']
    
    def normalize(self, content: bytes, source_info: Dict) -> List[Dict]:
        try:
            from pdfminer.high_level import extract_text
            from io import BytesIO
            
            text = extract_text(BytesIO(content))
            
            if not text:
                return []
            
            # PDF 轉文字通常無法保持結構
            # 這裡簡化為一筆記錄，包含完整文字
            return [{
                'source': source_info.get('url', ''),
                'full_text': text.strip()
            }]
        except ImportError:
            # pdfminer 未安裝
            return [{
                'error': 'pdfminer not installed',
                'source': source_info.get('url', '')
            }]
        except Exception as e:
            return [{
                'error': str(e),
                'source': source_info.get('url', '')
            }]