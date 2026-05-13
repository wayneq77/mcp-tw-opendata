import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
from db.connection import get_connection
from .fetch_cache import ensure_dataset_cached, _download_and_parse, _get_source_url
import json


def get_dataset(dataset_id: str, sample_rows: int = 5) -> dict:
    """
    取得資料集詳細資訊。
    若 dataset_rows 尚無資料，自動從 source_url 下載並快取。
    """
    conn = get_connection()
    cur = conn.cursor()

    # 取得資料集 metadata
    cur.execute("""
        SELECT
            dataset_id, name_zh, name_en, description, agency,
            primary_domain, domains, update_freq, quality_tier, formats,
            license, source_url, row_count, last_sync
        FROM datasets
        WHERE dataset_id = %s
    """, (dataset_id,))

    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return {"error": "Dataset not found"}

    source_url = row[11]
    row_count = row[12]

    result = {
        "dataset_id": row[0],
        "name": row[1],
        "name_en": row[2],
        "description": row[3],
        "agency": row[4],
        "primary_domain": row[5],
        "domains": row[6] if row[6] else [],
        "update_freq": row[7],
        "quality_tier": row[8],
        "formats": row[9] if row[9] else [],
        "license": row[10],
        "source_url": source_url,
        "row_count": row_count,
        "last_sync": row[13].isoformat() if row[13] else None,
        "schema": {"columns": [], "sample_rows": []},
        "sample": {"columns": [], "rows": []}
    }

    # 若需要 sample，先確保已快取
    if sample_rows > 0:
        # 先檢查本地快取
        cur.execute("SELECT COUNT(*) FROM dataset_rows WHERE dataset_id = %s", (dataset_id,))
        cached = cur.fetchone()[0]

        if cached == 0 and source_url:
            # Lazy download
            cur.close()
            conn.close()
            ensure_dataset_cached(dataset_id)
            conn = get_connection()
            cur = conn.cursor()

        # 取得 schema 和樣本資料
        cur.execute("SELECT row_data FROM dataset_rows WHERE dataset_id = %s LIMIT %s",
                    (dataset_id, sample_rows))
        sample_data = []
        all_keys = set()
        for row_data_row in cur.fetchall():
            data = row_data_row[0]
            if isinstance(data, str):
                data = json.loads(data)
            sample_data.append(data)
            all_keys.update(data.keys())

        result["schema"]["columns"] = sorted(list(all_keys))
        result["schema"]["sample_rows"] = sample_data
        result["sample"]["columns"] = sorted(list(all_keys))
        result["sample"]["rows"] = [[data.get(col, "") for col in sorted(all_keys)] for data in sample_data]

    cur.close()
    conn.close()

    return result
