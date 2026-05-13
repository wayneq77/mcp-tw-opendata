from .base import BaseNormalizer
from typing import Dict, List, Any
import json

class GeoJSONNormalizer(BaseNormalizer):
    """GeoJSON 檔案正規化"""
    
    def can_handle(self, content: bytes, content_type: str) -> bool:
        return content_type in ['application/geo+json', 'application/vnd.geo+json', '.geojson', '.json'] or self._looks_like_geojson(content)
    
    def _looks_like_geojson(self, content: bytes) -> bool:
        try:
            text = content.decode('utf-8', errors='ignore')
            data = json.loads(text)
            return 'type' in data and 'FeatureCollection' in data.get('type', '')
        except:
            return False
    
    def normalize(self, content: bytes, source_info: Dict) -> List[Dict]:
        text = content.decode('utf-8', errors='replace')
        data = json.loads(text)
        
        records = []
        
        # 處理 FeatureCollection
        if data.get('type') == 'FeatureCollection':
            features = data.get('features', [])
            for feature in features:
                record = feature.get('properties', {})
                
                # 如果有幾何資料，提取座標
                geometry = feature.get('geometry', {})
                if geometry:
                    record['_geometry_type'] = geometry.get('type')
                    
                    coords = geometry.get('coordinates')
                    if coords:
                        if geometry.get('type') == 'Point':
                            record['_longitude'] = coords[0]
                            record['_latitude'] = coords[1]
                        else:
                            record['_coordinates'] = coords
                
                if record:
                    records.append(self._clean_record(record))
        
        return records