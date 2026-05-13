from .base import BaseNormalizer
from typing import Dict, List, Any
import csv
import io
import json
import charset_normalizer

class CSVNormalizer(BaseNormalizer):
    """CSV 檔案正規化"""
    
    def can_handle(self, content: bytes, content_type: str) -> bool:
        return content_type in ['text/csv', 'application/csv', '.csv'] or self._looks_like_csv(content)
    
    def _looks_like_csv(self, content: bytes) -> bool:
        """簡單判斷是否像 CSV"""
        try:
            # 嘗試解碼
            text = content.decode('utf-8')
        except:
            try:
                text = content.decode('big5')
            except:
                text = content.decode('latin1', errors='ignore')
        
        lines = text.strip().split('\n')
        if len(lines) < 1:
            return False
        
        # 檢查是否有多個分隔符（逗號、分號）
        first_line = lines[0]
        if ',' in first_line or ';' in first_line or '\t' in first_line:
            return True
        
        return False
    
    def normalize(self, content: bytes, source_info: Dict) -> List[Dict]:
        # 自動偵測編碼
        result = charset_normalizer.from_bytes(content)
        encoding = result.best().encoding if result.best() else 'utf-8'
        
        text = content.decode(encoding, errors='replace')
        
        # 嘗試不同的分隔符
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return []
        
        # 偵測分隔符
        delimiter = self._detect_delimiter(lines[0])
        
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        
        headers = next(reader)
        headers = [h.strip().strip('"') for h in headers]
        
        records = []
        for row in reader:
            if len(row) != len(headers):
                continue
            
            record = {}
            for i, header in enumerate(headers):
                if header:
                    value = row[i].strip().strip('"')
                    record[header] = self._clean_value(value)
            
            if record:
                records.append(self._clean_record(record))
        
        return records
    
    def _detect_delimiter(self, line: str) -> str:
        """偵測分隔符"""
        comma_count = line.count(',')
        semicolon_count = line.count(';')
        tab_count = line.count('\t')
        
        if tab_count >= comma_count and tab_count >= semicolon_count:
            return '\t'
        elif semicolon_count >= comma_count:
            return ';'
        else:
            return ','