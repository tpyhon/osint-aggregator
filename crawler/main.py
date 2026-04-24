from db import get_active_sources, save_article, save_crawl_log, update_last_crawled
from fetcher import fetch_feed
from nvd_fetcher import fetch_nvd_recent, save_nvd_articles

def crawl_all():
    sources = get_active_sources()
    print(f"[INFO] {len(sources)}件のソースをクロール開始")

    for source in sources:
        print(f"[INFO] クロール中: {source['name']}")
        articles_found = 0
        articles_new = 0

        try:
            articles = fetch_feed(source)
            articles_found = len(articles)

            for article in articles:
                result = save_article(
                    source_id   = source["id"],
                    url         = article["url"],
                    title       = article["title"],
                    body_raw    = article["body_raw"],
                    published_at= article["published_at"],
                    language    = article["language"],
                )
                if result:  # Noneでなければ新規保存できた
                    articles_new += 1

            update_last_crawled(source["id"])
            save_crawl_log(source["id"], articles_found, articles_new, "success")
            print(f"[OK] {source['name']}: 取得={articles_found} 新規={articles_new}")

        except Exception as e:
            save_crawl_log(source["id"], articles_found, articles_new, "failed", str(e))
            print(f"[ERROR] {source['name']}: {e}")
            
            # NVD API（RSS廃止のため個別処理）
    print("[INFO] クロール中: NVD API")
    try:
        nvd_articles = fetch_nvd_recent()
        nvd_new = save_nvd_articles(nvd_articles)
        print(f"[OK] NVD API: 取得={len(nvd_articles)} 新規={nvd_new}")
    except Exception as e:
        print(f"[ERROR] NVD API: {e}")

if __name__ == "__main__":
    crawl_all()
