from db import get_connection

def cleanup_old_articles(days: int = 5):
    """5日以上前の記事を削除（ブックマーク済みは除外）"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM articles
                WHERE published_at < NOW() - INTERVAL '%s days'
                  AND is_bookmarked = FALSE
                RETURNING id
            """, (days,))
            deleted = cur.rowcount
            conn.commit()
            print(f"[OK] {deleted}件の古い記事を削除しました")
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_old_articles(days=5)
