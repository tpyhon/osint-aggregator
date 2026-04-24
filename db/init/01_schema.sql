-- クロール対象ソース管理
CREATE TABLE sources (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    url             TEXT NOT NULL UNIQUE,
    feed_type       VARCHAR(50) NOT NULL,  -- 'rss', 'atom', 'scrape'
    region          VARCHAR(20) NOT NULL,  -- 'domestic', 'international'
    category        VARCHAR(100),          -- 'vulnerability', 'incident', 'tech', 'news'
    is_active       BOOLEAN DEFAULT TRUE,
    crawl_interval  INTEGER DEFAULT 720,   -- 分単位（720=12時間）
    last_crawled_at TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 取得記事（生データ）
CREATE TABLE articles (
    id              SERIAL PRIMARY KEY,
    source_id       INTEGER NOT NULL REFERENCES sources(id),
    url             TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    body_raw        TEXT,                  -- 取得した生本文（HTML or テキスト）
    published_at    TIMESTAMP WITH TIME ZONE,
    fetched_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_processed    BOOLEAN DEFAULT FALSE, -- LLM処理済みフラグ
    language        VARCHAR(10),           -- 'ja', 'en'
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LLM処理結果（要約・分類）
CREATE TABLE summaries (
    id              SERIAL PRIMARY KEY,
    article_id      INTEGER NOT NULL REFERENCES articles(id) UNIQUE,
    summary_ja      TEXT,                  -- 日本語要約
    severity        VARCHAR(20),           -- 'critical', 'high', 'medium', 'low', 'info'
    cve_ids         TEXT[],                -- CVE番号配列 例: {'CVE-2024-1234'}
    cvss_score      NUMERIC(4,1),          -- 例: 9.8
    llm_model       VARCHAR(100),          -- 使用したモデル名
    processed_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- タグマスタ
CREATE TABLE tags (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE, -- '脆弱性','インシデント','新技術' etc
    slug            VARCHAR(100) NOT NULL UNIQUE, -- 'vulnerability','incident','new-tech'
    color           VARCHAR(7),                   -- '#FF5733' UIのバッジ色
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 記事とタグの中間テーブル
CREATE TABLE article_tags (
    article_id      INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    tag_id          INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    confidence      NUMERIC(3,2),          -- LLMの分類確信度 0.00~1.00
    PRIMARY KEY (article_id, tag_id)
);

-- クロール実行ログ
CREATE TABLE crawl_logs (
    id              SERIAL PRIMARY KEY,
    source_id       INTEGER NOT NULL REFERENCES sources(id),
    started_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at     TIMESTAMP WITH TIME ZONE,
    articles_found  INTEGER DEFAULT 0,     -- 取得記事数
    articles_new    INTEGER DEFAULT 0,     -- 新規記事数（重複除外後）
    status          VARCHAR(20),           -- 'success', 'partial', 'failed'
    error_message   TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
