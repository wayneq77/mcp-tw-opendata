import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    """建立資料庫連線"""
    database_url = os.getenv("DATABASE_URL", "")
    
    if database_url:
        # 解析 DATABASE_URL
        # 格式: postgresql://user:pass@host:port/dbname
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
        if match:
            return psycopg2.connect(
                host=match.group(3),
                port=int(match.group(4)),
                database=match.group(5),
                user=match.group(1),
                password=match.group(2)
            )
    
    # Fallback: 使用環境變數
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),  # Docker Compose 服務名
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "tw_opendata"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "")
    )