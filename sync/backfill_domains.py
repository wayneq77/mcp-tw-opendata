#!/usr/bin/env python3
"""
回填 primary_domain 為 NULL 的資料集
使用 domain_classifier 的關鍵字規則重新分類
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from classifiers.domain_classifier import classify
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:CHANGE_TO_A_STRONG_PASSWORD_HERE@localhost:5432/tw_opendata')


def get_conn():
    import re
    m = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if m:
        return psycopg2.connect(host=m.group(3), port=m.group(4),
                                database=m.group(5), user=m.group(1), password=m.group(2))
    raise ValueError("Invalid DATABASE_URL")


def main():
    conn = get_conn()
    cur = conn.cursor()

    # 取得所有 NULL domain 的資料集
    cur.execute("""
        SELECT dataset_id, name_zh, description
        FROM datasets
        WHERE primary_domain IS NULL
    """)
    rows = cur.fetchall()
    print(f"需要回填的資料集: {len(rows)} 筆")

    if not rows:
        print("全部已有分類！")
        return

    updated = 0
    stats = {}

    for dataset_id, name_zh, description in rows:
        text = f"{name_zh or ''} {description or ''}"
        domain = classify(text)

        cur.execute("""
            UPDATE datasets SET primary_domain = %s, updated_at = NOW()
            WHERE dataset_id = %s AND primary_domain IS NULL
        """, (domain, dataset_id))

        stats[domain] = stats.get(domain, 0) + 1
        updated += 1

        if updated % 5000 == 0:
            conn.commit()
            print(f"  已回填 {updated}/{len(rows)}...", flush=True)

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n回填完成！共 {updated} 筆")
    print("\n分類分布:")
    for domain, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {domain}: {count}")


if __name__ == "__main__":
    main()
