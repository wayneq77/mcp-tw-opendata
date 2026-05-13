"""
一次性 bulk import：將 /tmp/data_gov_full.csv 的 53,011 筆資料集寫入 PostgreSQL
"""
import csv
import time
import re
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values

# ── 領域分類 mapping（服務分類 → domain key）───────────────────────────────
DOMAIN_MAP = {
    "公共資訊": None,                       # 無精確 domain，留 NULL
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

BATCH_SIZE = 500

def parse_formats(raw: str) -> list:
    if not raw:
        return []
    return [f.strip() for f in raw.split(";") if f.strip()]

def clean_text(val) -> str | None:
    if val is None:
        return None
    t = val.strip()
    return t if t else None

def row_to_record(row: dict) -> tuple:
    dataset_id   = clean_text(row.get("資料集識別碼"))
    name_zh      = clean_text(row.get("資料集名稱"))
    description  = clean_text(row.get("資料集描述"))
    agency       = clean_text(row.get("提供機關"))
    svc_class    = clean_text(row.get("服務分類"))
    quality      = clean_text(row.get("品質檢測"))
    formats_raw  = clean_text(row.get("檔案格式"))
    source_url   = clean_text(row.get("資料下載網址"))
    update_freq  = clean_text(row.get("更新頻率"))
    license      = clean_text(row.get("授權方式"))
    row_count_raw = clean_text(row.get("資料量"))

    primary_domain = DOMAIN_MAP.get(svc_class, None)

    formats = parse_formats(formats_raw) if formats_raw else []

    # row_count：第一個分號前的數字（取第一個）
    row_count = None
    if row_count_raw:
        try:
            first_val = row_count_raw.split(";")[0].strip()
            if first_val.isdigit():
                row_count = int(first_val)
        except Exception:
            pass

    return (
        dataset_id,
        name_zh,
        description,
        agency,
        primary_domain,
        quality,
        formats,
        source_url,
        update_freq,
        license,
        row_count,
    )


def main():
    t0 = time.time()
    written = 0
    errors = 0

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="tw_opendata",
        user="postgres",
        password="CHANGE_TO_A_STRONG_PASSWORD_HERE",
    )
    conn.autocommit = False
    cur = conn.cursor()

    insert_sql = """
    INSERT INTO datasets (
        dataset_id, name_zh, description, agency, primary_domain,
        quality_tier, formats, source_url, update_freq, license, row_count
    ) VALUES %s
    ON CONFLICT (dataset_id) DO NOTHING
    """

    batch = []
    with open("/tmp/data_gov_full.csv", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                record = row_to_record(row)
                batch.append(record)
            except Exception as e:
                errors += 1
                print(f"  [SKIP] row error: {e}")
                continue

            if len(batch) >= BATCH_SIZE:
                execute_values(cur, insert_sql, batch)
                conn.commit()
                written += len(batch)
                elapsed = time.time() - t0
                rate = written / elapsed if elapsed > 0 else 0
                print(f"  ✓ 寫入 {written:,} 筆（{rate:.0f} 筆/秒）")
                batch = []

    # 最後一批
    if batch:
        execute_values(cur, insert_sql, batch)
        conn.commit()
        written += len(batch)
        print(f"  ✓ 寫入 {written:,} 筆")

    cur.close()
    conn.close()

    elapsed = time.time() - t0
    print(f"\n✅ 完成！寫入 {written:,} 筆，錯誤 {errors} 筆，耗時 {elapsed:.1f}s")

    # ── 驗證 ─────────────────────────────────────────────────────────────
    print("\n── 驗證 ──")
    try:
        conn2 = psycopg2.connect(
            host="localhost", port=5432, database="tw_opendata",
            user="postgres", password="CHANGE_TO_A_STRONG_PASSWORD_HERE"
        )
        cur2 = conn2.cursor()
        cur2.execute("SELECT COUNT(*) FROM datasets")
        total = cur2.fetchone()[0]
        print(f"  datasets 表總筆數：{total:,}")

        cur2.execute("""
            SELECT primary_domain, COUNT(*) as cnt
            FROM datasets
            WHERE primary_domain IS NOT NULL
            GROUP BY primary_domain
            ORDER BY cnt DESC
        """)
        print("  primary_domain 分布：")
        for row in cur2.fetchall():
            print(f"    {row[0]:<30} {row[1]:>6,} 筆")
        conn2.close()
    except Exception as e:
        print(f"  驗證查詢失敗：{e}")


if __name__ == "__main__":
    main()