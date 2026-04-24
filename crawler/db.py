import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def get_active_sources():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, url, feed_type, region, category
                FROM sources
                WHERE is_active = TRUE
            """)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()

def save_article(source_id, url, title, body_raw, published_at, language):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO articles
                    (source_id, url, title, body_raw, published_at, language)
                VALUES
                    (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
                RETURNING id
            """, (source_id, url, title, body_raw, published_at, language))
            result = cur.fetchone()
            conn.commit()
            return result[0] if result else None
    finally:
        conn.close()

def save_crawl_log(source_id, articles_found, articles_new, status, error_message=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO crawl_logs
                    (source_id, articles_found, articles_new, status, error_message, finished_at)
                VALUES
                    (%s, %s, %s, %s, %s, NOW())
            """, (source_id, articles_found, articles_new, status, error_message))
            conn.commit()
    finally:
        conn.close()

def update_last_crawled(source_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sources SET last_crawled_at = NOW()
                WHERE id = %s
            """, (source_id,))
            conn.commit()
    finally:
        conn.close()
