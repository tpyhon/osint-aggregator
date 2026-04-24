import time
import subprocess
import sys

def get_unprocessed_count():
    from db import get_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM articles WHERE is_processed = FALSE")
            return cur.fetchone()[0]
    finally:
        conn.close()

if __name__ == "__main__":
    from summarizer import summarize_all

    batch = 10        # 1回あたりの処理件数
    wait  = 10        # バッチ間の待機秒数

    while True:
        count = get_unprocessed_count()
        print(f"\n[INFO] 未処理残り: {count}件")

        if count == 0:
            print("[完了] 全記事の処理が終わりました")
            break

        summarize_all(limit=batch)
        print(f"[INFO] {wait}秒待機...")
        time.sleep(wait)
