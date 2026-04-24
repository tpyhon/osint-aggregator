import feedparser
import requests
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

def detect_language(url, region):
    """regionからざっくり言語を判定"""
    if region == "domestic":
        return "ja"
    return "en"

def normalize_datetime(entry):
    """feedparserの日付をdatetimeに変換"""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def fetch_feed(source):
    """RSSフィードを取得して記事リストを返す"""
    results = []
    try:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries:
            url = entry.get("link", "")
            title = entry.get("title", "")
            body_raw = entry.get("summary", "") or entry.get("description", "")
            published_at = normalize_datetime(entry)
            language = detect_language(source["url"], source["region"])

            if not url or not title:
                continue

            results.append({
                "url": url,
                "title": title,
                "body_raw": body_raw,
                "published_at": published_at,
                "language": language,
            })
    except Exception as e:
        raise RuntimeError(f"フィード取得失敗: {source['url']} / {e}")

    return results
