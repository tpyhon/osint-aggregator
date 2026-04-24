import time
from db import get_connection
from llm_processor import process_article
from slack_notifier import notify_article, notify_summary


def get_unprocessed_articles(limit=10):
    """未処理記事を取得"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, a.title, a.body_raw, a.language
                FROM articles a
                LEFT JOIN summaries s ON a.id = s.article_id
                WHERE a.is_processed = FALSE
                  AND s.article_id IS NULL
                ORDER BY a.published_at DESC
                LIMIT %s
            """, (limit,))
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()

def save_summary(article_id, result):
    """LLM処理結果をsummariesとarticle_tagsに保存"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # summariesに保存（既存のCVSSスコアは上書きしない）
            cur.execute("""
                INSERT INTO summaries
                    (article_id, summary_ja, severity, cve_ids, llm_model)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (article_id) DO UPDATE SET
                    summary_ja = EXCLUDED.summary_ja,
                    severity   = EXCLUDED.severity,
                    cve_ids    = EXCLUDED.cve_ids,
                    llm_model  = EXCLUDED.llm_model,
                    processed_at = NOW()
            """, (
                article_id,
                result.get("summary_ja"),
                result.get("severity"),
                result.get("cve_ids", []),
                "gemma-4-26b-a4b-it",
            ))

            # article_tagsに保存
            for tag_slug in result.get("tags", []):
                cur.execute("""
                    SELECT id FROM tags WHERE slug = %s
                """, (tag_slug,))
                tag_row = cur.fetchone()
                if tag_row:
                    cur.execute("""
                        INSERT INTO article_tags (article_id, tag_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (article_id, tag_row[0]))

            # 処理済みフラグを立てる
            cur.execute("""
                UPDATE articles SET is_processed = TRUE WHERE id = %s
            """, (article_id,))

            conn.commit()
    finally:
        conn.close()

def summarize_all(limit=10):
    articles = get_unprocessed_articles(limit)
    print(f"[INFO] 未処理記事: {len(articles)}件")

    success = 0
    failed = 0
    new_critical = 0
    new_high = 0

    for article in articles:
        print(f"[INFO] 処理中: {article['title'][:60]}...")
        try:
            result = process_article(article["title"], article["body_raw"] or "")
            save_summary(article["id"], result)
            success += 1
            print(f"[OK] severity={result.get('severity')} tags={result.get('tags')}")

            # CriticalとHighはSlackに通知
            severity = result.get("severity")
            if severity in ("critical", "high"):
                notify_article({
                    "title":      article["title"],
                    "url":        get_article_url(article["id"]),
                    "region":     get_article_region(article["id"]),
                    "source_name":get_article_source(article["id"]),
                    "severity":   severity,
                    "cve_ids":    result.get("cve_ids", []),
                    "cvss_score": None,
                    "tags":       result.get("tags", []),
                    "summary_ja": result.get("summary_ja"),
                })
                if severity == "critical":
                    new_critical += 1
                else:
                    new_high += 1

            time.sleep(4)
        except Exception as e:
            failed += 1
            print(f"[ERROR] article_id={article['id']}: {e}")
            time.sleep(5)

    notify_summary(new_critical, new_high)
    print(f"[完了] 成功={success} 失敗={failed}")

