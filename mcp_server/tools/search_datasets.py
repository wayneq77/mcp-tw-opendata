import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, List, Any
from db.connection import get_connection

def search_datasets(
    query: str = "",
    domain: Optional[str] = None,
    agency: Optional[str] = None,
    limit: int = 20,
    quality: Optional[str] = None,
    update_freq: Optional[str] = None,
    fmt: Optional[str] = None
) -> dict:
    """搜尋資料集（改用純 ILIKE 對中文有效）"""
    conn = get_connection()
    cur = conn.cursor()
    
    # 建構 WHERE 條件
    conditions = []
    params = []
    
    if query:
        # 改用純 ILIKE 搜尋（plainto_tsquery 對中文無效）
        # 對每個 token 個別做 AND 匹配（所有 token 都要出現在 name/desc 中）
        tokens = query.strip().split()
        token_conditions = []
        for token in tokens:
            p = f"%{token}%"
            token_conditions.append(
                "(name_zh ILIKE %s OR name_en ILIKE %s OR description ILIKE %s)"
            )
            params.extend([p, p, p])
        
        if token_conditions:
            conditions.append("(" + " AND ".join(token_conditions) + ")")
    
    if domain:
        conditions.append("primary_domain = %s")
        params.append(domain)
    
    if agency:
        conditions.append("agency ILIKE %s")
        params.append(f"%{agency}%")
    
    if quality:
        conditions.append("quality_tier = %s")
        params.append(quality)
    
    if update_freq:
        conditions.append("update_freq = %s")
        params.append(update_freq)
    
    if fmt:
        conditions.append("%s = ANY(formats)")
        params.append(fmt)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # 排序：按 last_sync 降序
    order_by = "ORDER BY last_sync DESC NULLS LAST"
    
    sql = f"""
        SELECT 
            dataset_id, name_zh, name_en, description, agency,
            primary_domain, domains, update_freq, quality_tier, formats,
            license, source_url, row_count, last_sync
        FROM datasets
        WHERE {where_clause}
        {order_by}
        LIMIT %s
    """
    params.append(limit)
    
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    hits = []
    for row in rows:
        hits.append({
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
            "source_url": row[11],
            "row_count": row[12],
            "last_sync": row[13].isoformat() if row[13] else None
        })
    
    return {"hits": hits, "count": len(hits)}