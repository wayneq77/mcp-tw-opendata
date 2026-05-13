"""
Lazy Download & Cache Module
當查詢 dataset_rows 時，若無資料則自動從 source_url 下載並快取
"""
import sys
import os

# 加入 tools 的父目錄（mcp_server）到 sys.path
_tools_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _tools_dir)

import json
import csv
import io
import re
from db.connection import get_connection
import requests

# 下載設定
DOWNLOAD_TIMEOUT = 60
MAX_RETRIES = 3


def _get_source_url(dataset_id: str):
    """取得資料集的 source_url"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT source_url FROM datasets WHERE dataset_id = %s", (dataset_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def _download_and_parse(url: str):
    """
    從 URL 下載並解析 CSV/JSON
    Returns: (rows_as_dicts, column_names) or None if failed
    """
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=DOWNLOAD_TIMEOUT, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; MCP-TW-Local/1.0)',
                'Accept': 'text/csv, application/json, */*'
            })
            resp.raise_for_status()
            content = resp.text.strip()

            if not content:
                return None

            # 嘗試 CSV
            if ',' in content[:500] or '\t' in content[:500]:
                try:
                    reader = csv.DictReader(io.StringIO(content))
                    rows = [dict(row) for row in reader]
                    if rows:
                        columns = list(rows[0].keys())
                        return rows, columns
                except Exception:
                    pass

            # 嘗試 JSON (陣列)
            try:
                data = json.loads(content)
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], dict):
                        columns = list(data[0].keys())
                        return data, columns
            except Exception:
                pass

            return None

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                import time as _time
                _time.sleep(2 ** attempt)
            else:
                return None

    return None


def _store_rows(dataset_id: str, rows: list) -> int:
    """將下載的資料列存入 dataset_rows 表"""
    if not rows:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    stored = 0
    for row in rows:
        row_json = json.dumps(row, ensure_ascii=False)
        try:
            cur.execute("""
                INSERT INTO dataset_rows (dataset_id, row_data)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (dataset_id, row_json))
            stored += 1
        except Exception:
            pass

    conn.commit()
    cur.close()
    conn.close()
    return stored


def ensure_dataset_cached(dataset_id: str):
    """
    確保資料集已快取。若未快取，自動下載。
    Returns: (success, message)
    """
    # 1. 先檢查是否已有快取
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM dataset_rows WHERE dataset_id = %s", (dataset_id,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    if count > 0:
        return True, f"已有快取 ({count} 列)"

    # 2. 取得 source_url
    source_url = _get_source_url(dataset_id)
    if not source_url:
        return False, "無 source_url"

    # 3. 下載並解析
    result = _download_and_parse(source_url)
    if not result:
        return False, f"下載失敗: {source_url}"

    rows, columns = result

    # 4. 存入資料庫
    stored = _store_rows(dataset_id, rows)

    # 5. 更新 datasets.row_count
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE datasets SET row_count = %s, last_sync = NOW()
        WHERE dataset_id = %s
    """, (stored, dataset_id))
    conn.commit()
    cur.close()
    conn.close()

    return True, f"已下載並快取 {stored} 列"
