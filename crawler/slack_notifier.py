import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

SEVERITY_EMOJI = {
    "critical": "🚨",
    "high":     "⚠️",
    "medium":   "🔶",
    "low":      "🔷",
    "info":     "ℹ️",
}

def notify_article(article: dict):
    """記事をSlackに通知"""
    if not WEBHOOK_URL:
        print("[WARN] SLACK_WEBHOOK_URLが設定されていません")
        return

    severity = article.get("severity", "info")
    emoji = SEVERITY_EMOJI.get(severity, "ℹ️")
    region = "🇯🇵 国内" if article.get("region") == "domestic" else "🌏 海外"
    cve_str = " ".join(article.get("cve_ids") or [])
    tags_str = " ".join([f"`{t}`" for t in (article.get("tags") or [])])

    text = f"""
{emoji} *[{severity.upper()}] {article['title']}*
{region} | {article.get('source_name', '')}
{article['url']}
"""
    if cve_str:
        text += f"CVE: `{cve_str}`\n"
    if article.get("cvss_score"):
        text += f"CVSS: `{article['cvss_score']}`\n"
    if tags_str:
        text += f"タグ: {tags_str}\n"
    if article.get("summary_ja"):
        text += f"\n{article['summary_ja']}\n"

    payload = {"text": text.strip()}
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Slack通知失敗: {e}")

def notify_summary(new_critical: int, new_high: int):
    """クロール完了サマリーを通知"""
    if not WEBHOOK_URL:
        return
    if new_critical == 0 and new_high == 0:
        return

    text = f"🛡 *OSINT Aggregator クロール完了*\n"
    if new_critical > 0:
        text += f"🚨 Critical: {new_critical}件\n"
    if new_high > 0:
        text += f"⚠️ High: {new_high}件\n"

    payload = {"text": text.strip()}
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Slack通知失敗: {e}")
