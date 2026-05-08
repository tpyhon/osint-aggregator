import time
import os
from db import get_connection
from llm_processor import build_analysis_prompt, process_article

def get_unanalyzed_articles(limit=20):
    """analysis_jaが未生成の処理済み記事を取得"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    a.id, a.title, a.url, a.body_raw,
                    s.summary_ja, s.severity, s.cve_ids, s.cvss_score
                FROM articles a
                JOIN summaries s ON a.id = s.article_id
                WHERE a.is_processed = TRUE
                  AND (s.analysis_ja IS NULL OR s.analysis_ja = '')
                ORDER BY a.published_at DESC
                LIMIT %s
            """, (limit,))
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()

def save_analysis(article_id: int, analysis_text: str, model: str):
    """analysis_jaをDBに保存"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE summaries
                SET analysis_ja = %s,
                    analysis_generated_at = NOW()
                WHERE article_id = %s
            """, (analysis_text, article_id))
            conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    from google import genai

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model  = os.getenv("GEMINI_MODEL", "gemma-4-26b-a4b-it")

    articles = get_unanalyzed_articles(limit=20)
    print(f"[INFO] 未解析記事: {len(articles)}件")

    success = 0
    failed  = 0

    for article in articles:
        print(f"[INFO] Geminiでの解析: 記事ID {article['id']} {article['title'][:50]}")
        try:
            prompt   = build_analysis_prompt(article)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            analysis_text = response.text
            footer = f"\n\n---\n📄 [原文を読む]({article['url']})"
            save_analysis(article["id"], analysis_text + footer, model)
            success += 1
            print(f"[OK] article_id={article['id']}")
            time.sleep(5)  # Gemini無料枠のレート制限対策
        except Exception as e:
            failed += 1
            print(f"[ERROR] article_id={article['id']}: {e}")
            time.sleep(10)

    print(f"[完了] 成功={success} 失敗={failed}")
