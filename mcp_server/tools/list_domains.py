import sys
import os

# Add the parent directory to the path so we can import relative modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, List, Any
from db.connection import get_connection

def list_domains() -> dict:
    """列出所有 19 個領域"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT key, name_zh, name_en, role, scope, typical_questions, anchor_examples
        FROM domains
        ORDER BY name_zh
    """)
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    domains = []
    for row in rows:
        domains.append({
            "key": row[0],
            "name_zh": row[1],
            "name_en": row[2],
            "role": row[3],
            "scope": row[4],
            "typical_questions": row[5] if row[5] else [],
            "anchor_examples": row[6] if row[6] else []
        })
    
    return {"domains": domains}