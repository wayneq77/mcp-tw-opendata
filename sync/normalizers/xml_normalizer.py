from .base import BaseNormalizer
from typing import Dict, List, Any
from lxml import etree

class XMLNormalizer(BaseNormalizer):
    """XML 檔案正規化"""
    
    def can_handle(self, content: bytes, content_type: str) -> bool:
        return content_type in ['application/xml', 'text/xml', '.xml'] or self._looks_like_xml(content)
    
    def _looks_like_xml(self, content: bytes) -> bool:
        text = content.decode('utf-8', errors='ignore').strip()
        return text.startswith('<?xml') or text.startswith('<')
    
    def normalize(self, content: bytes, source_info: Dict) -> List[Dict]:
        try:
            root = etree.fromstring(content)
        except etree.XMLSyntaxError:
            return []
        
        records = []
        
        # 嘗試找到記錄列表
        # 常見的 record wrapper tags
        record_tags = ['record', 'item', 'row', 'entry', 'data', 'record']
        
        for tag in record_tags:
            elements = root.findall(f'.//{tag}')
            if elements:
                for elem in elements:
                    record = self._element_to_dict(elem)
                    if record:
                        records.append(self._clean_record(record))
                break
        
        # 如果找不到特定的 record tags，嘗試取所有第一層子元素
        if not records:
            for child in root:
                if etree.iselement(child):
                    record = self._element_to_dict(child)
                    if record:
                        records.append(self._clean_record(record))
        
        return records
    
    def _element_to_dict(self, element) -> Dict:
        """將 XML element 轉為 dict"""
        record = {}
        
        # 子元素或屬性
        for child in element:
            tag = child.tag
            if len(child) > 0:
                # 有子元素，遞迴處理
                value = self._element_to_dict(child)
            else:
                # 文字內容
                value = child.text.strip() if child.text else ""
            
            record[tag] = value
        
        # 如果有屬性
        for attr, value in element.attrib.items():
            record[f'@{attr}'] = value
        
        return record