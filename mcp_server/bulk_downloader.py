#!/usr/bin/env python3
"""
Bulk Download - Immediate write on success
"""
import sys, os, json, csv, io, time, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from db.connection import get_connection

WORKERS = 10
COMMIT_EVERY = 50   # 每下載完 50 個就 commit 一次
CSV_PATH = "/home/wayneq77/Downloads/datagovtw_dataset_20260512.csv"


def load_datasets():
    ds = []
    with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            url = row.get('資料下載網址', '').strip()
            if url and url.startswith('http'):
                ds.append({
                    'dataset_id': row.get('資料集識別碼', '').strip(),
                    'source_url': url,
                })
    return ds


def download_one(url):
    for attempt in range(2):
        try:
            resp = requests.get(url, timeout=25, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; MCP-TW/1.0)',
                'Accept': 'text/csv, application/json, */*'
            })
            if resp.status_code == 404:
                return None, '404'
            resp.raise_for_status()
            content = resp.text.strip()
            if not content:
                return None, 'empty'

            if ',' in content[:300] or '\t' in content[:300]:
                try:
                    rows = [dict(r) for r in csv.DictReader(io.StringIO(content))]
                    if rows:
                        return rows, 'ok'
                except Exception:
                    pass
            try:
                data = json.loads(content)
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    return data, 'ok'
            except Exception:
                pass
            return None, 'parse_error'
        except Exception:
            if attempt < 1:
                time.sleep(1)
            else:
                return None, 'err'
    return None, 'timeout'


def main():
    t0 = time.time()
    print(f"[{datetime.now()}] 開始", flush=True)

    all_ds = load_datasets()
    total = len(all_ds)
    print(f"共 {total} 個", flush=True)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT dataset_id FROM dataset_rows")
    cached = set(r[0] for r in cur.fetchall())
    cur.close()
    print(f"已有快取: {len(cached)}", flush=True)

    to_dl = [ds for ds in all_ds if ds['dataset_id'] not in cached]
    print(f"需下載: {len(to_dl)}", flush=True)

    if not to_dl:
        conn.close()
        return

    stats = {'ok': 0, 'fail': 0}
    total_rows = 0
    done = 0
    buf = []  # [(dataset_id, rows)]

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(download_one, ds['source_url']): ds for ds in to_dl}

        for future in as_completed(futures):
            ds = futures[future]
            rows, status = future.result()

            if status == 'ok' and rows:
                stats['ok'] += 1
                buf.append((ds['dataset_id'], rows))
            else:
                stats['fail'] += 1

            done += 1

            # 每 COMMIT_EVERY 個就寫入一次
            if done % COMMIT_EVERY == 0:
                elapsed = time.time() - t0
                rate = done / elapsed
                eta = (total - done) / rate / 60 if rate > 0 else 0
                print(f"  [{done}/{total}] ok:{stats['ok']} fail:{stats['fail']} "
                      f"buf:{len(buf)} total_rows:{total_rows} ETA:{eta:.0f}min", flush=True)

            if len(buf) >= COMMIT_EVERY:
                # Write buffer
                cur2 = conn.cursor()
                for ds_id, rows2 in buf:
                    try:
                        cur2.execute("DELETE FROM dataset_rows WHERE dataset_id = %s", (ds_id,))
                    except Exception:
                        pass
                    for row in rows2:
                        try:
                            cur2.execute("INSERT INTO dataset_rows (dataset_id, row_data) VALUES (%s, %s)",
                                       (ds_id, json.dumps(row, ensure_ascii=False)))
                        except Exception:
                            pass
                    try:
                        cur2.execute("UPDATE datasets SET row_count=%s,last_sync=NOW() WHERE dataset_id=%s",
                                   (len(rows2), ds_id))
                    except Exception:
                        pass
                conn.commit()
                cur2.close()
                total_rows += sum(len(r) for _, r in buf)
                buf = []

    # 最後寫入
    if buf:
        cur2 = conn.cursor()
        for ds_id, rows2 in buf:
            try:
                cur2.execute("DELETE FROM dataset_rows WHERE dataset_id = %s", (ds_id,))
            except Exception:
                pass
            for row in rows2:
                try:
                    cur2.execute("INSERT INTO dataset_rows (dataset_id, row_data) VALUES (%s, %s)",
                               (ds_id, json.dumps(row, ensure_ascii=False)))
                except Exception:
                    pass
            try:
                cur2.execute("UPDATE datasets SET row_count=%s,last_sync=NOW() WHERE dataset_id=%s",
                           (len(rows2), ds_id))
            except Exception:
                pass
        conn.commit()
        cur2.close()
        total_rows += sum(len(r) for _, r in buf)

    conn.close()
    elapsed = time.time() - t0
    print(f"\n完成！{elapsed:.0f}s ({elapsed/60:.1f}min)", flush=True)
    print(f"  ok:{stats['ok']} fail:{stats['fail']} rows:{total_rows}", flush=True)


if __name__ == "__main__":
    main()
