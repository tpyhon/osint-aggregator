import requests
import time
from datetime import datetime, timezone, timedelta
from db import get_connection

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

def fetch_nvd_recent():
    """NVD APIから直近2日分のCVEを取得"""
    now = datetime.now(timezone.utc)
    pub_start = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S.000")
    pub_end = now.strftime("%Y-%m-%dT%H:%M:%S.000")

    params = {
        "pubStartDate": pub_start,
        "pubEndDate": pub_end,
        "resultsPerPage": 50,
    }

    try:
        resp = requests.get(NVD_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"NVD API取得失敗: {e}")

    results = []
    for item in data.get("vulnerabilities", []):
        cve = item.get("cve", {})
        cve_id = cve.get("id", "")

        # タイトル（説明文の先頭）
        descriptions = cve.get("descriptions", [])
        title = next(
            (d["value"] for d in descriptions if d["lang"] == "en"),
            cve_id
        )

        # CVSS スコア取得
        cvss_score = None
        metrics = cve.get("metrics", {})
        for key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            if key in metrics and metrics[key]:
                cvss_score = metrics[key][0].get("cvssData", {}).get("baseScore")
                break

        # 公開日
        published_str = cve.get("published", "")
        try:
            published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        except Exception:
            published_at = datetime.now(timezone.utc)

        url = f"https://nvd.nist.gov/vuln/detail/{cve_id}"

        results.append({
            "cve_id": cve_id,
            "url": url,
            "title": f"{cve_id}: {title[:200]}",
            "body_raw": title,
            "published_at": published_at,
            "cvss_score": cvss_score,
            "language": "en",
        })

    return results

def save_nvd_articles(results):
    """NVE記事をDBに保存してsummariesにCVSS情報も入れる"""
    conn = get_connection()
    new_count = 0
    try:
        with conn.cursor() as cur:
            # NVDのsource_idを取得（無効化してても参照はできる）
            cur.execute("SELECT id FROM sources WHERE name = 'NVD'")
            row = cur.fetchone()
            if not row:
                print("[WARN] NVDソースがDBに存在しません")
                return 0
            source_id = row[0]

            for item in results:
                cur.execute("""
                    INSERT INTO articles
                        (source_id, url, title, body_raw, published_at, language)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                    RETURNING id
                """, (
                    source_id,
                    item["url"],
                    item["title"],
                    item["body_raw"],
                    item["published_at"],
                    item["language"],
                ))
                result = cur.fetchone()
                if result:
                    article_id = result[0]
                    new_count += 1
                    # summariesにCVSS情報を先入れ
                    if item["cvss_score"]:
                        cur.execute("""
                            INSERT INTO summaries
                                (article_id, cve_ids, cvss_score, llm_model)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (article_id) DO NOTHING
                        """, (
                            article_id,
                            [item["cve_id"]],
                            item["cvss_score"],
                            "nvd-api",
                        ))
                # APIレート制限対策（6req/秒まで）
                time.sleep(0.2)

        conn.commit()
    finally:
        conn.close()
    return new_count
