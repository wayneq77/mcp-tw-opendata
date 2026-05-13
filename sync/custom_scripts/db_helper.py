import os
import psycopg2
from psycopg2.extras import execute_values
import json
import re

def get_db_connection():
    # Use environment variable from the container
    database_url = os.getenv('DATABASE_URL', '')
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
    if match:
        return psycopg2.connect(
            host=match.group(3),
            port=match.group(4),
            database=match.group(5),
            user=match.group(1),
            password=match.group(2)
        )
    raise ValueError("Invalid DATABASE_URL format")

def register_custom_dataset(dataset_id: str, name_zh: str, description: str = "", primary_domain: str = "custom", agency: str = ""):
    """註冊一個新的資料集索引到 datasets 表格"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT dataset_id FROM datasets WHERE dataset_id = %s", (dataset_id,))
            exists = cur.fetchone()
            
            if exists:
                cur.execute("""
                    UPDATE datasets 
                    SET name_zh = %s, description = %s, primary_domain = %s, agency = %s, last_sync = NOW(), updated_at = NOW()
                    WHERE dataset_id = %s
                """, (name_zh, description, primary_domain, agency, dataset_id))
                print(f"✅ 更新資料集中繼資料: {dataset_id}")
            else:
                cur.execute("""
                    INSERT INTO datasets (dataset_id, name_zh, description, primary_domain, agency, last_sync)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (dataset_id, name_zh, description, primary_domain, agency))
                print(f"✅ 新增資料集中繼資料: {dataset_id}")
        conn.commit()
    finally:
        conn.close()

def insert_dataset_rows(dataset_id: str, rows: list):
    """
    將資料安全寫入 dataset_rows 表格。
    這個函數會執行 UPSERT 或全量覆蓋。為了簡單，這會清除該資料集的舊資料並重新寫入。
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 清除舊資料 (因為這是 custom fetcher，我們假設它每次抓都是最新全量)
            cur.execute("DELETE FROM dataset_rows WHERE dataset_id = %s", (dataset_id,))
            
            # 準備批量插入
            records = [(dataset_id, json.dumps(row, ensure_ascii=False)) for row in rows]
            
            execute_values(cur, """
                INSERT INTO dataset_rows (dataset_id, row_data)
                VALUES %s
            """, records)
            
            # 更新資料集筆數
            cur.execute("""
                UPDATE datasets SET row_count = %s WHERE dataset_id = %s
            """, (len(rows), dataset_id))
            
            print(f"✅ 成功寫入 {len(rows)} 筆資料到 {dataset_id}")
        conn.commit()
    finally:
        conn.close()
