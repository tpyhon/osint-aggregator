import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_API_KEY"))
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def export_to_notion(article: dict) -> bool:
    """記事をNotionデータベースに追加"""
    try:
        # タグを文字列に変換
        tags_str = ", ".join(article.get("tags") or [])
        cve_str  = ", ".join(article.get("cve_ids") or [])

        properties = {
            "タイトル": {
                "title": [{"text": {"content": article["title"][:2000]}}]
            },
            "URL": {
                "url": article["url"]
            },
            "ソース": {
                "rich_text": [{"text": {"content": article.get("source_name") or ""}}]
            },
            "地域": {
                "rich_text": [{"text": {"content": "国内" if article.get("region") == "domestic" else "海外"}}]
            },
            "深刻度": {
                "select": {"name": article["severity"].upper()} if article.get("severity") else {"select": None}
            },
            "CVE": {
                "rich_text": [{"text": {"content": cve_str}}]
            },
            "タグ": {
                "rich_text": [{"text": {"content": tags_str}}]
            },
            "保存日": {
                "date": {"start": article["published_at"][:10]}
            },
        }

        # 本文（要約）をページコンテンツとして追加
        children = []
        if article.get("summary_ja"):
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": article["summary_ja"]}}]
                }
            })

        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties,
            children=children,
        )
        return True
    except Exception as e:
        print(f"[ERROR] Notion export失敗: {e}")
        return False
