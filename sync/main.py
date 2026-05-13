"""
Sync Worker Main - 資料同步主程式
每天從 data.gov.tw 同步所有資料集到本地資料庫
"""
import os
import sys
import json
import time
import argparse
import traceback
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 加入路徑
sys.path.insert(0, os.path.dirname(__file__))

from fetchers.data_gov_fetcher import DataGovFetcher
from classifiers.domain_classifier import classify

# PostgreSQL 相關
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL', '')


def get_db_connection():
    """建立資料庫連線"""
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if match:
        return psycopg2.connect(
            host=match.group(3),
            port=match.group(4),
            database=match.group(5),
            user=match.group(1),
            password=match.group(2)
        )
    raise ValueError("Invalid DATABASE_URL format")


class SyncWorker:
    """同步 Worker"""

    def __init__(self):
        self.fetcher = DataGovFetcher()
        self.batch_size = 100  # 每批處理的資料集數量

    def run_full_sync(self):
        """執行完整同步"""
        start_time = datetime.now()
        print(f"[{start_time}] 開始同步...", flush=True)

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # 1. 取得資料集目錄
            print("抓取資料集目錄（串流下載 ~68MB CSV）...", flush=True)
            datasets, total = self.fetcher.fetch_datasets_catalog()
            print(f"共取得 {total} 筆資料集", flush=True)

            if total == 0:
                print("警告：取得 0 筆資料集，可能是 API 問題，跳過本次同步", flush=True)
                cur.execute("""
                    INSERT INTO sync_logs (sync_date, status, datasets_added, datasets_updated, error_message)
                    VALUES (NOW(), 'skipped', 0, 0, '取得 0 筆資料集，API 可能異常')
                """)
                conn.commit()
                return

            # 2. 處理每個資料集
            added = 0
            updated = 0
            errors = 0

            for i, dataset in enumerate(datasets, 1):
                try:
                    was_new = self._sync_dataset(cur, dataset)
                    if was_new:
                        added += 1
                    else:
                        updated += 1

                    if i % 1000 == 0:
                        print(f"  進度: {i}/{total} (新增:{added} 更新:{updated} 失敗:{errors})", flush=True)
                        conn.commit()

                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        print(f"  處理資料集 {dataset.get('dataset_id')} 失敗: {e}", flush=True)

            # 3. 記錄同步日誌
            cur.execute("""
                INSERT INTO sync_logs (sync_date, status, datasets_added, datasets_updated, error_message)
                VALUES (NOW(), 'completed', %s, %s, %s)
            """, (added, updated, f"errors: {errors}" if errors > 0 else None))

            conn.commit()
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"同步完成！新增:{added} 更新:{updated} 失敗:{errors} 耗時:{elapsed:.1f}s", flush=True)

        except Exception as e:
            print(f"同步失敗: {e}", flush=True)
            traceback.print_exc()
            try:
                cur.execute("""
                    INSERT INTO sync_logs (sync_date, status, datasets_added, datasets_updated, error_message)
                    VALUES (NOW(), 'failed', 0, 0, %s)
                """, (str(e)[:500],))
                conn.commit()
            except Exception:
                pass
        finally:
            cur.close()
            conn.close()

    def _sync_dataset(self, cur, dataset_info: dict):
        """同步單一資料集。回傳 True 表示新增，False 表示更新"""
        dataset_id = dataset_info.get('dataset_id')
        if not dataset_id:
            return False

        # 1. 決定領域分類
        name = dataset_info.get('name_zh', '') or ''
        description = dataset_info.get('description', '') or ''
        combined_text = f"{name} {description}"

        # 優先使用 fetcher 提供的 domain，沒有才用 classifier
        primary_domain = dataset_info.get('primary_domain')
        if not primary_domain:
            primary_domain = classify(combined_text)

        # 2. 檢查是否已存在
        cur.execute("SELECT dataset_id FROM datasets WHERE dataset_id = %s", (dataset_id,))
        exists = cur.fetchone()

        formats_val = dataset_info.get('formats')
        if isinstance(formats_val, list):
            formats_val = formats_val if formats_val else None
        else:
            formats_val = None

        if exists:
            # 更新
            cur.execute("""
                UPDATE datasets
                SET name_zh = %s, name_en = %s, description = %s, agency = %s,
                    primary_domain = COALESCE(%s, primary_domain),
                    update_freq = %s, quality_tier = %s, formats = %s,
                    license = %s, source_url = %s, last_sync = NOW(), updated_at = NOW()
                WHERE dataset_id = %s
            """, (
                dataset_info.get('name_zh'),
                dataset_info.get('name_en'),
                dataset_info.get('description'),
                dataset_info.get('agency'),
                primary_domain,
                dataset_info.get('update_freq'),
                dataset_info.get('quality_tier'),
                formats_val,
                dataset_info.get('license'),
                dataset_info.get('source_url'),
                dataset_id
            ))
            return False
        else:
            # 新增
            cur.execute("""
                INSERT INTO datasets (dataset_id, name_zh, name_en, description, agency,
                    primary_domain, update_freq, quality_tier, formats, license, source_url, last_sync)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                dataset_id,
                dataset_info.get('name_zh'),
                dataset_info.get('name_en'),
                dataset_info.get('description'),
                dataset_info.get('agency'),
                primary_domain,
                dataset_info.get('update_freq'),
                dataset_info.get('quality_tier'),
                formats_val,
                dataset_info.get('license'),
                dataset_info.get('source_url')
            ))
            return True


def parse_cron_hour(cron_expr: str) -> int:
    """從 cron 表達式取出小時（簡易解析）。例: '0 3 * * *' → 3"""
    parts = cron_expr.strip().split()
    if len(parts) >= 2:
        try:
            return int(parts[1])
        except ValueError:
            pass
    return 3  # 預設凌晨 3 點


def main():
    parser = argparse.ArgumentParser(description="Twinkle Hub 本地版 - 資料同步 Worker")
    parser.add_argument('--schedule', help='Cron expression (只用小時欄位)')
    parser.add_argument('--once', action='store_true', help='單次執行後退出')
    args = parser.parse_args()

    worker = SyncWorker()

    if args.once:
        # 單次執行模式
        print("=== 單次同步模式 ===", flush=True)
        worker.run_full_sync()
        return

    if args.schedule:
        # 排程模式：保持 process alive，每天指定時間執行
        target_hour = parse_cron_hour(args.schedule)
        print(f"=== 排程模式 ===", flush=True)
        print(f"Cron: {args.schedule} → 每天 {target_hour}:00 執行同步", flush=True)
        print(f"Process 啟動時間: {datetime.now()}", flush=True)
        print(f"等待下次執行時間...", flush=True)

        last_run_date = None

        while True:
            now = datetime.now()
            today = now.date()

            # 到達執行時間且今天還沒跑過
            if now.hour == target_hour and last_run_date != today:
                print(f"\n{'='*60}", flush=True)
                print(f"排程觸發: {now}", flush=True)
                print(f"{'='*60}", flush=True)
                try:
                    worker.run_full_sync()
                except Exception as e:
                    print(f"同步異常: {e}", flush=True)
                    traceback.print_exc()
                last_run_date = today
                print(f"下次執行: 明天 {target_hour}:00", flush=True)

            # 每 60 秒檢查一次
            time.sleep(60)
    else:
        # 無參數：單次執行
        worker.run_full_sync()


if __name__ == "__main__":
    main()