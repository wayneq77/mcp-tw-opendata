import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, List, Any
from db.connection import get_connection
from .fetch_cache import ensure_dataset_cached
import json
import re


def query_rows(
    dataset_id: str,
    where: Optional[str] = None,
    columns: Optional[List[str]] = None,
    limit: int = 100
) -> dict:
    """
    查詢資料列。
    若 dataset_rows 尚無資料，自動從 source_url 下載並快取。
    """
    conn = get_connection()
    cur = conn.cursor()

    # 限制 limit 防止濫用
    limit = min(limit, 1000)

    # 驗證 dataset_id（防止 SQL injection）
    if not re.match(r'^[a-zA-Z0-9_-]+$', dataset_id):
        return {"error": "Invalid dataset_id"}

    # 先檢查本地快取
    cur.execute("SELECT COUNT(*) FROM dataset_rows WHERE dataset_id = %s", (dataset_id,))
    cached = cur.fetchone()[0]

    if cached == 0:
        # Lazy download
        cur.close()
        conn.close()
        success, msg = ensure_dataset_cached(dataset_id)
        if not success:
            return {"error": f"無法下載資料集: {msg}", "dataset_id": dataset_id}
        conn = get_connection()
        cur = conn.cursor()

    # 建構查詢
    select_cols = "*"
    if columns:
        # 驗證 column 名稱
        safe_cols = [c for c in columns if re.match(r'^[a-zA-Z0-9_\u4e00-\u9fff]+$', c)]
        if safe_cols:
            select_cols = ", ".join(safe_cols)

    sql = f"""
        SELECT row_data
        FROM dataset_rows
        WHERE dataset_id = %s
    """
    params = [dataset_id]

    if where:
        # 簡單的 WHERE 處理
        sql += " AND row_data @> %s"
        try:
            where_json = json.loads(where)
            params.append(json.dumps(where_json))
        except:
            sql += " AND row_data ->> 'dummy' = %s"
            params.append(where)

    sql += f" LIMIT {limit}"

    try:
        cur.execute(sql, params)
        rows = cur.fetchall()

        # 提取所有鍵
        all_keys = set()
        for row in rows:
            data = row[0]
            if isinstance(data, str):
                data = json.loads(data)
            all_keys.update(data.keys())

        result_columns = sorted(list(all_keys)) if not columns else columns

        # 組裝結果
        result_rows = []
        for row in rows:
            data = row[0]
            if isinstance(data, str):
                data = json.loads(data)
            row_values = [str(data.get(col, "")) for col in result_columns]
            result_rows.append(row_values)

        cur.close()
        conn.close()

        return {
            "columns": result_columns,
            "rows": result_rows,
            "row_count_returned": len(result_rows)
        }
    except Exception as e:
        cur.close()
        conn.close()
        return {"error": str(e)}
