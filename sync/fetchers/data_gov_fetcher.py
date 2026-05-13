"""
Data.gov.tw API Fetcher
從政府開放資料平台取得資料集清單與下載檔案
串流下載 68MB CSV，不會一次讀進記憶體
"""
import csv
import io
import requests
from typing import Dict, List, Optional, Tuple
import time

# Data.gov.tw API 端點（正確的 CSV 匯出端點）
BASE_URL = "https://data.gov.tw"
API_CSV_EXPORT = f"{BASE_URL}/api/v2/rest/dataset/export"
API_DATASET_DETAIL = f"{BASE_URL}/api/v2/rest/datastore"


class DataGovFetcher:
    """Data.gov.tw 資料抓取器"""

    # 領域分類 mapping（服務分類 → domain key）
    DOMAIN_MAP = {
        "公共資訊": "gov_publication",
        "生活安全及品質": "public_safety",
        "購屋及遷徙": "realestate_land",
        "交通及通訊": "transport",
        "投資理財": "economy_business",
        "休閒旅遊": "culture_tourism_sport",
        "就醫": "health_food",
        "開創事業": "economy_business",
        "求學及進修": "education_research",
        "求職及就業": "labor_employment",
        "老年安養": "social_population",
        "服兵役": "judicial_legal",
        "生育保健": "health_food",
        "選舉及投票": "social_population",
        "生命禮儀": "social_population",
        "出生及收養": "social_population",
        "婚姻": "social_population",
        "退休": "labor_employment",
    }

    def __init__(self, timeout: int = 120, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; MCP-TW-OpenData/1.0)',
            'Accept': 'text/csv, application/json, */*'
        })

    def _retry_request(self, url: str, stream: bool = False, **kwargs) -> Optional[requests.Response]:
        """帶重試的 HTTP 請求"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, stream=stream, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt
                    print(f"  下載重試 ({attempt+1}/{self.max_retries}): {e}", flush=True)
                    time.sleep(wait)
                else:
                    print(f"  下載失敗 ({self.max_retries} 次重試後): {e}", flush=True)
                    return None
        return None

    def fetch_datasets_catalog(self) -> Tuple[List[Dict], int]:
        """
        從 CSV 匯出端點取得資料集目錄
        使用串流下載避免記憶體爆掉

        Returns:
            (datasets_list, total_count)
        """
        try:
            url = API_CSV_EXPORT
            print(f"  下載端點: {url}", flush=True)

            # 串流下載
            response = self._retry_request(url, stream=True)
            if not response:
                print("  無法取得 CSV 回應", flush=True)
                return [], 0

            content_length = response.headers.get('Content-Length', 'unknown')
            print(f"  Content-Length: {content_length} bytes", flush=True)

            # 串流讀取所有內容（用 utf-8-sig 處理 BOM）
            # 因為 csv.DictReader 需要完整的文字流，所以先讀完
            raw_bytes = b''
            downloaded = 0
            for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                raw_bytes += chunk
                downloaded += len(chunk)
                if downloaded % (10 * 1024 * 1024) == 0:  # 每 10MB 印一次
                    print(f"  已下載 {downloaded / 1024 / 1024:.0f} MB...", flush=True)

            print(f"  下載完成: {downloaded / 1024 / 1024:.1f} MB", flush=True)

            # 解碼（utf-8-sig 自動處理 BOM）
            text = raw_bytes.decode('utf-8-sig')
            del raw_bytes  # 釋放記憶體

            # 解析 CSV
            reader = csv.DictReader(io.StringIO(text))
            datasets = []
            for row in reader:
                svc_class = row.get("服務分類", "").strip()
                formats_raw = row.get("檔案格式", "").strip()

                datasets.append({
                    'dataset_id': row.get("資料集識別碼", "").strip(),
                    'name_zh': row.get("資料集名稱", "").strip() or None,
                    'name_en': None,
                    'description': row.get("資料集描述", "").strip() or None,
                    'agency': row.get("提供機關", "").strip() or None,
                    'primary_domain': self.DOMAIN_MAP.get(svc_class, None),
                    'update_freq': row.get("更新頻率", "").strip() or None,
                    'formats': [f.strip() for f in formats_raw.split(";") if f.strip()] if formats_raw else [],
                    'license': row.get("授權方式", "").strip() or None,
                    'source_url': row.get("資料下載網址", "").strip() or None,
                    'quality_tier': row.get("品質檢測", "").strip() or None,
                    'row_count': self._parse_row_count(row.get("資料量", "")),
                })

            total = len(datasets)
            print(f"  解析完成: {total} 筆資料集", flush=True)
            del text  # 釋放記憶體
            return datasets, total

        except Exception as e:
            print(f"Error fetching catalog: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return [], 0

    def _parse_row_count(self, raw: str) -> Optional[int]:
        """解析資料量欄位，取第一個分號前的數字"""
        if not raw:
            return None
        try:
            first_val = raw.split(";")[0].strip()
            if first_val.isdigit():
                return int(first_val)
        except Exception:
            pass
        return None

    def fetch_dataset_detail(self, dataset_id: str) -> Optional[Dict]:
        """取得單一資料集的詳細資訊"""
        try:
            url = f"{API_DATASET_DETAIL}/{dataset_id}"
            response = self._retry_request(url)

            if not response:
                return None

            return response.json()

        except Exception as e:
            print(f"Error fetching dataset {dataset_id}: {e}")
            return None

    def download_file(self, url: str) -> Optional[bytes]:
        """下載檔案內容"""
        try:
            response = self._retry_request(url)
            if response:
                return response.content
            return None
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None

    def detect_format(self, url: str) -> str:
        """從 URL 偵測檔案格式"""
        url_lower = url.lower()
        if url_lower.endswith('.csv'):
            return '.csv'
        elif url_lower.endswith('.json'):
            return '.json'
        elif url_lower.endswith('.xml'):
            return '.xml'
        elif url_lower.endswith('.pdf'):
            return '.pdf'
        elif url_lower.endswith('.geojson'):
            return '.geojson'
        return 'unknown'