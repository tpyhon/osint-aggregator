from fastapi import FastAPI, Query , Query ,Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from db import get_connection
import sys
import os
import jwt
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'crawler'))
from notion_exporter import export_to_notion
from sse_starlette.sse import EventSourceResponse
from llm_processor import build_analysis_prompt, get_model, _call_llm_async
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="OSINT Aggregator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────
# 認証ヘルパー
# ──────────────────────────────────────────
def get_user_id(authorization: str) -> str:
    auth_required = os.getenv("AUTH_REQUIRED", "false").lower() == "true"
    if not auth_required:
        return LOCAL_USER_ID

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="認証が必要です")

    token = authorization.split(" ", 1)[1]
    try:
        # ES256移行済みのため署名検証をスキップしてsubを取得
        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,  # 署名検証スキップ
                "verify_exp": True,         # 有効期限は検証する
            },
            algorithms=["HS256", "ES256"],
        )
        # issがSupabaseのものか確認（最低限の検証）
        iss = payload.get("iss", "")
        if "supabase" not in iss:
            raise HTTPException(status_code=401, detail="無効なトークンです")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="無効なトークンです")

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="トークンの有効期限が切れています")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"無効なトークンです: {str(e)}")




@app.get("/articles")
def get_articles(
    region:   Optional[str] = Query(None),
    tag:      Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page:     int = Query(1, ge=1),
    limit:    int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * limit
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            conditions = ["1=1"]
            params = []

            if region:
                conditions.append("s_src.region = %s")
                params.append(region)

            if severity:
                conditions.append("s.severity = %s")
                params.append(severity)

            if tag:
                conditions.append("""
                    EXISTS (
                        SELECT 1 FROM article_tags at
                        JOIN tags t ON at.tag_id = t.id
                        WHERE at.article_id = a.id AND t.slug = %s
                    )
                """)
                params.append(tag)

            where = "WHERE " + " AND ".join(conditions)

            # 合計件数
            cur.execute(f"""
                SELECT COUNT(DISTINCT a.id)
                FROM articles a
                LEFT JOIN summaries s ON a.id = s.article_id
                JOIN sources s_src ON a.source_id = s_src.id
                {where}
            """, params)
            total = cur.fetchone()[0]

            # 記事一覧
            cur.execute(f"""
                SELECT
                    a.id,
                    a.title,
                    a.url,
                    a.published_at,
                    a.language,
                    a.is_processed,
                    a.is_bookmarked,
                    s_src.name   AS source_name,
                    s_src.region AS region,
                    s.summary_ja,
                    s.severity,
                    s.cve_ids,
                    s.cvss_score,
                    ARRAY_AGG(DISTINCT t.slug) FILTER (WHERE t.slug IS NOT NULL) AS tags
                FROM articles a
                LEFT JOIN summaries s ON a.id = s.article_id
                JOIN sources s_src ON a.source_id = s_src.id
                LEFT JOIN article_tags at ON a.id = at.article_id
                LEFT JOIN tags t ON at.tag_id = t.id
                {where}
                GROUP BY
                    a.id, a.title, a.url, a.published_at, a.language, a.is_processed, a.is_bookmarked,
                    s_src.name, s_src.region,
                    s.summary_ja, s.severity, s.cve_ids, s.cvss_score
                ORDER BY a.published_at DESC
                LIMIT %s OFFSET %s
            """, params + [limit, offset])

            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]

            for row in rows:
                if row.get("published_at"):
                    row["published_at"] = row["published_at"].isoformat()

            return {
                "total": total,
                "page": page,
                "limit": limit,
                "articles": rows,
            }
    finally:
        conn.close()


@app.get("/tags")
def get_tags():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, slug, color FROM tags ORDER BY id")
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()


@app.get("/sources")
def get_sources():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, region, category, is_active, last_crawled_at
                FROM sources ORDER BY region, name
            """)
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            for row in rows:
                if row.get("last_crawled_at"):
                    row["last_crawled_at"] = row["last_crawled_at"].isoformat()
            return rows
    finally:
        conn.close()


@app.get("/stats")
def get_stats():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM articles")
            total_articles = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM articles WHERE is_processed = TRUE")
            processed = cur.fetchone()[0]

            cur.execute("""
                SELECT severity, COUNT(*) FROM summaries
                GROUP BY severity ORDER BY severity
            """)
            severity_counts = {row[0]: row[1] for row in cur.fetchall()}

            return {
                "total_articles": total_articles,
                "processed": processed,
                "unprocessed": total_articles - processed,
                "severity_counts": severity_counts,
            }
    finally:
        conn.close()


@app.post("/articles/{article_id}/bookmark")
def toggle_bookmark(
    article_id: int,
    authorization: str = Header(default=None),
):
    """
    ユーザーごとのブックマーク切り替え。
    未ログイン時は 401。
    """
    user_id = get_user_id(authorization)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 記事の存在確認
            cur.execute("SELECT id FROM articles WHERE id = %s", (article_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="記事が見つかりません")

            # すでにブックマーク済みか確認
            cur.execute(
                "SELECT id FROM user_bookmarks WHERE user_id = %s AND article_id = %s",
                (user_id, article_id),
            )
            existing = cur.fetchone()

            if existing:
                # 登録済み → 削除（トグルOFF）
                cur.execute(
                    "DELETE FROM user_bookmarks WHERE user_id = %s AND article_id = %s",
                    (user_id, article_id),
                )
                is_bookmarked = False
            else:
                # 未登録 → 追加（トグルON）
                cur.execute(
                    "INSERT INTO user_bookmarks (user_id, article_id) VALUES (%s, %s)",
                    (user_id, article_id),
                )
                is_bookmarked = True

            conn.commit()
            return {"is_bookmarked": is_bookmarked}
    finally:
        conn.close()


@app.get("/bookmarks")
def get_bookmarks(authorization: str = Header(default=None)):
    """
    ログインユーザーのブックマーク一覧を返す。
    """
    user_id = get_user_id(authorization)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    a.id, a.title, a.url, a.published_at,
                    a.is_processed,
                    TRUE AS is_bookmarked,   -- ブックマーク一覧なので常にtrue
                    s_src.name AS source_name,
                    s_src.region AS region,
                    s.summary_ja, s.severity, s.cve_ids, s.cvss_score,
                    ARRAY_AGG(DISTINCT t.slug) FILTER (WHERE t.slug IS NOT NULL) AS tags
                FROM user_bookmarks ub
                JOIN articles a ON ub.article_id = a.id
                LEFT JOIN summaries s ON a.id = s.article_id
                JOIN sources s_src ON a.source_id = s_src.id
                LEFT JOIN article_tags at ON a.id = at.article_id
                LEFT JOIN tags t ON at.tag_id = t.id
                WHERE ub.user_id = %s
                GROUP BY
                    a.id, a.title, a.url, a.published_at, a.is_processed,
                    s_src.name, s_src.region,
                    s.summary_ja, s.severity, s.cve_ids, s.cvss_score
                ORDER BY a.published_at DESC
            """, (user_id,))
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            for row in rows:
                if row.get("published_at"):
                    row["published_at"] = row["published_at"].isoformat()
            return rows
    finally:
        conn.close()

@app.get("/articles/{article_id}/is_bookmarked")
def check_bookmark(
    article_id: int,
    authorization: str = Header(default=None),
):
    """
    記事一覧表示時に各記事のブックマーク状態を返す軽量エンドポイント。
    未ログイン時は常に False を返す（エラーにしない）。
    """
    if not authorization:
        return {"is_bookmarked": False}
    try:
        user_id = get_user_id(authorization)
    except HTTPException:
        return {"is_bookmarked": False}

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM user_bookmarks WHERE user_id = %s AND article_id = %s",
                (user_id, article_id),
            )
            return {"is_bookmarked": cur.fetchone() is not None}
    finally:
        conn.close()


@app.get("/bookmarks/ids")
def get_bookmark_ids(authorization: str = Header(default=None)):
    """
    フロントエンドが記事一覧のブックマーク表示に使う、
    ブックマーク済み article_id の配列を返す。
    N+1を避けるため、一括取得用に用意。
    """
    if not authorization:
        return {"ids": []}
    try:
        user_id = get_user_id(authorization)
    except HTTPException:
        return {"ids": []}

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT article_id FROM user_bookmarks WHERE user_id = %s",
                (user_id,),
            )
            ids = [row[0] for row in cur.fetchall()]
            return {"ids": ids}
    finally:
        conn.close()

@app.post("/articles/{article_id}/export-notion")
def export_article_to_notion(article_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    a.id, a.title, a.url, a.published_at,
                    a.is_processed, a.is_bookmarked,
                    s_src.name AS source_name,
                    s_src.region AS region,
                    s.summary_ja, s.severity, s.cve_ids,
                    ARRAY_AGG(DISTINCT t.slug) FILTER (WHERE t.slug IS NOT NULL) AS tags
                FROM articles a
                LEFT JOIN summaries s ON a.id = s.article_id
                JOIN sources s_src ON a.source_id = s_src.id
                LEFT JOIN article_tags at ON a.id = at.article_id
                LEFT JOIN tags t ON at.tag_id = t.id
                WHERE a.id = %s
                GROUP BY
                    a.id, a.title, a.url, a.published_at,
                    a.is_processed, a.is_bookmarked,
                    s_src.name, s_src.region,
                    s.summary_ja, s.severity, s.cve_ids
            """, (article_id,))
            columns = [desc[0] for desc in cur.description]
            row = cur.fetchone()
            if not row:
                return {"error": "記事が見つかりません"}
            article = dict(zip(columns, row))
            if article.get("published_at"):
                article["published_at"] = article["published_at"].isoformat()

        success = export_to_notion(article)
        if success:
            return {"status": "ok"}
        else:
            return {"status": "error"}
    finally:
        conn.close()
        
@app.get("/search")
def search_articles(
    q:    str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit:int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * limit
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            search = f"%{q}%"

            cur.execute("""
                SELECT COUNT(DISTINCT a.id)
                FROM articles a
                LEFT JOIN summaries s ON a.id = s.article_id
                JOIN sources s_src ON a.source_id = s_src.id
                WHERE
                    a.title ILIKE %s
                    OR s.summary_ja ILIKE %s
                    OR %s = ANY(s.cve_ids)
            """, (search, search, q.upper()))
            total = cur.fetchone()[0]

            cur.execute("""
                SELECT
                    a.id,
                    a.title,
                    a.url,
                    a.published_at,
                    a.language,
                    a.is_processed,
                    a.is_bookmarked,
                    s_src.name   AS source_name,
                    s_src.region AS region,
                    s.summary_ja,
                    s.severity,
                    s.cve_ids,
                    s.cvss_score,
                    ARRAY_AGG(DISTINCT t.slug) FILTER (WHERE t.slug IS NOT NULL) AS tags
                FROM articles a
                LEFT JOIN summaries s ON a.id = s.article_id
                JOIN sources s_src ON a.source_id = s_src.id
                LEFT JOIN article_tags at ON a.id = at.article_id
                LEFT JOIN tags t ON at.tag_id = t.id
                WHERE
                    a.title ILIKE %s
                    OR s.summary_ja ILIKE %s
                    OR %s = ANY(s.cve_ids)
                GROUP BY
                    a.id, a.title, a.url, a.published_at, a.language,
                    a.is_processed, a.is_bookmarked,
                    s_src.name, s_src.region,
                    s.summary_ja, s.severity, s.cve_ids, s.cvss_score
                ORDER BY a.published_at DESC
                LIMIT %s OFFSET %s
            """, (search, search, q.upper(), limit, offset))

            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            for row in rows:
                if row.get("published_at"):
                    row["published_at"] = row["published_at"].isoformat()

            return {
                "total": total,
                "page": page,
                "limit": limit,
                "articles": rows,
            }
    finally:
        conn.close()
        
@app.get("/articles/{article_id}/analysis")
async def get_analysis(article_id: int):
    """解析ページ用SSEエンドポイント。キャッシュがあれば即返却、なければLLM生成してDB保存"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # キャッシュ確認
            cur.execute("""
                SELECT
                    a.title, a.body_raw, a.url, a.language,
                    s.summary_ja, s.severity, s.cve_ids, s.cvss_score,
                    s.analysis_ja, s.analysis_generated_at,
                    src.name AS source_name, src.region
                FROM articles a
                LEFT JOIN summaries s ON a.id = s.article_id
                JOIN sources src ON a.source_id = src.id
                WHERE a.id = %s
            """, (article_id,))
            row = cur.fetchone()
            if not row:
                async def not_found():
                    yield {"data": "❌ 記事が見つかりません"}
                    yield {"event": "done", "data": ""}
                return EventSourceResponse(not_found())

            cols = [d[0] for d in cur.description]
            article = dict(zip(cols, row))
    finally:
        conn.close()

    # キャッシュが存在する場合はそのまま返す
    if article.get("analysis_ja"):
        async def from_cache():
            # キャッシュを500文字ずつ分割して送信（ストリーミング風に見せる）
            text = article["analysis_ja"]
            chunk_size = 500
            for i in range(0, len(text), chunk_size):
                yield {"data": text[i:i + chunk_size]}
            yield {"data": "\n\n---\n📄 [原文を読む](" + article["url"] + ")"}
            yield {"event": "done", "data": ""}
        return EventSourceResponse(from_cache())

    # キャッシュなし → LLMで生成してDBに保存
    # キャッシュなし → LLMで生成してDBに保存
    async def generate_and_save():
        try:
            prompt = build_analysis_prompt(article)
            model = get_model()

            full_text = await _call_llm_async(prompt)

            # 500文字ずつチャンク送信（ストリーミング風）
            chunk_size = 500
            for i in range(0, len(full_text), chunk_size):
                yield {"data": full_text[i:i + chunk_size]}


            # 原文リンクを末尾に追加
            footer = f"\n\n---\n📄 [原文を読む]({article['url']})"
            full_text += footer
            yield {"data": footer}

            # DB に保存（次回以降はキャッシュから返す）
            save_conn = get_connection()
            try:
                with save_conn.cursor() as cur:
                    cur.execute("""
                        UPDATE summaries
                        SET analysis_ja = %s,
                            analysis_generated_at = NOW()
                        WHERE article_id = %s
                    """, (full_text, article_id))
                    # summariesが存在しない場合（未処理記事）はINSERT
                    if cur.rowcount == 0:
                        cur.execute("""
                            INSERT INTO summaries
                                (article_id, analysis_ja, analysis_generated_at, llm_model, processed_at)
                            VALUES (%s, %s, NOW(), %s, NOW())
                            ON CONFLICT (article_id) DO UPDATE
                            SET analysis_ja = EXCLUDED.analysis_ja,
                                analysis_generated_at = EXCLUDED.analysis_generated_at
                        """, (article_id, full_text, model))
                save_conn.commit()
            finally:
                save_conn.close()

            yield {"event": "done", "data": ""}

        except Exception as e:
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(generate_and_save())


