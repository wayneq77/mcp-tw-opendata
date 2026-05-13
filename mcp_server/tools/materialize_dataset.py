import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_connection
from .fetch_cache import ensure_dataset_cached
import json
import csv
import io
import re


def materialize_dataset(dataset_id: str, format: str = "json") -> dict:
    """下載並匯出完整資料集"""
    conn = get_connection()
    cur = conn.cursor()

    # 驗證 dataset_id
    if not re.match(r'^[a-zA-Z0-9_-]+$', dataset_id):
        return {"error": "Invalid dataset_id"}

    # 檢查資料集是否存在
    cur.execute("SELECT name_zh FROM datasets WHERE dataset_id = %s", (dataset_id,))
    ds_row = cur.fetchone()
    if not ds_row:
        cur.close()
        conn.close()
        return {"error": "Dataset not found"}

    # 確保已快取（lazy download）
    cur.execute("SELECT COUNT(*) FROM dataset_rows WHERE dataset_id = %s", (dataset_id,))
    cached = cur.fetchone()[0]

    if cached == 0:
        cur.close()
        conn.close()
        success, msg = ensure_dataset_cached(dataset_id)
        if not success:
            return {"error": f"無法下載資料集: {msg}", "dataset_id": dataset_id}
        conn = get_connection()
        cur = conn.cursor()

    # 取所有資料
    cur.execute("SELECT row_data FROM dataset_rows WHERE dataset_id = %s", (dataset_id,))

    rows = []
    columns_set = set()

    for row in cur.fetchall():
        data = row[0]
        if isinstance(data, str):
            data = json.loads(data)
        rows.append(data)
        columns_set.update(data.keys())

    cur.close()
    conn.close()

    columns = sorted(list(columns_set))

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return {
            "format": "csv",
            "data": output.getvalue(),
            "row_count": len(rows),
            "columns": columns
        }
    else:
        return {
            "format": "json",
            "data": rows,
            "row_count": len(rows),
            "columns": columns
        }
