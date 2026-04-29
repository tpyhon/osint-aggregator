# 🛡 DeepMole for OSINT

セキュリティ情報を自動収集・要約・分類するOSINTツールです。
国内外のセキュリティニュース・脆弱性情報をRSSとAPIで収集し、LLMで日本語要約・タグ付けして一覧表示します。

## 機能

- 国内外のセキュリティ情報を12時間ごとに自動収集
- LLMによる日本語要約・深刻度判定・自動タグ付け
- 国内/海外・タグ・深刻度でフィルタリング
- キーワード・CVE番号での検索
- ブックマーク機能
- ブックマーク記事のNotionエクスポート
- Critical/High記事のSlack即時通知
- 5日以上前の記事を自動削除

## 技術スタック

| 役割 | 技術 |
|---|---|
| クローラー | Python / feedparser |
| LLM処理 | Google Gemini API / Gemma |
| データベース | PostgreSQL（Docker） |
| バックエンド | FastAPI |
| フロントエンド | Next.js / Tailwind CSS |
| 自動実行 | Windowsタスクスケジューラ |

## ディレクトリ構成

## ディレクトリ構成

```
osint-aggregator/
├── crawler/
│   ├── main.py            # クローラーのエントリーポイント
│   ├── fetcher.py         # RSSフィード取得
│   ├── nvd_fetcher.py     # NVD API取得
│   ├── db.py              # DB接続・操作
│   ├── llm_processor.py   # LLM要約・タグ付け
│   ├── summarizer.py      # 未処理記事のLLM処理
│   ├── summarize_all.py   # 全件処理ループ
│   ├── slack_notifier.py  # Slack通知
│   ├── notion_exporter.py # Notionエクスポート
│   ├── cleanup.py         # 古い記事削除
│   └── .env               # 環境変数（Git管理外）
├── backend/
│   ├── main.py            # APIエンドポイント
│   ├── db.py              # DB接続
│   └── .env               # 環境変数（Git管理外）
├── frontend/
│   ├── app/
│   │   ├── page.tsx       # メイン画面
│   │   ├── types.ts       # 型定義
│   │   ├── lib/api.ts     # APIクライアント
│   │   └── components/
│   │       ├── ArticleCard.tsx    # 記事カード
│   │       └── SeverityBadge.tsx # 深刻度バッジ
├── db/
│   └── init/
│       └── 01_schema.sql  # DBスキーマ定義
├── docker-compose.yml     # PostgreSQL Docker設定
├── run_crawler.bat        # クローラー実行バッチ
└── run_summarizer.bat     # 要約処理実行バッチ
```


## セットアップ

### 必要なもの

- Docker Desktop
- Python 3.11
- Node.js 18以上
- Gemini API キー（Google AI Studio）
- Slack Webhook URL（任意）
- Notion API キー（任意）

### 手順

```bash
1. リポジトリをクローン
git clone https://github.com/tpyhon/osint-aggregator.git
cd osint-aggregator

2. DBを起動
Copydocker compose up -d

3. Python環境を構築
Copypython3.11 -m venv venv
venv\Scripts\activate
pip install -r crawler/requirements.txt
pip install -r backend/requirements.txt
pip install google-genai notion-client

4. 環境変数を設定

crawler/.envを作成します。

CopyDB_HOST=localhost
DB_PORT=5433
DB_NAME=osint
DB_USER=osint_user
DB_PASSWORD=osint_pass
GEMINI_API_KEY=your_api_key
SLACK_WEBHOOK_URL=your_webhook_url
NOTION_API_KEY=your_notion_key
NOTION_DATABASE_ID=your_database_id

backend/.envを作成します。

CopyDB_HOST=localhost
DB_PORT=5433
DB_NAME=osint
DB_USER=osint_user
DB_PASSWORD=osint_pass
NOTION_API_KEY=your_notion_key
NOTION_DATABASE_ID=your_database_id

5. クローラーを実行
Copycd crawler
python main.py
python summarize_all.py

6. バックエンドを起動
Copycd backend
uvicorn main:app --reload --port 8000

7. フロントエンドを起動
Copycd frontend
npm install
npm run dev
http://localhost:3000にアクセスします。

自動実行（Windowsタスクスケジューラ）
run_crawler.bat：12時間ごとに実行（クローラー＋古い記事削除）
run_summarizer.bat：クローラーの30分後に実行（LLM要約処理）

情報ソース
ソース	種別	地域
JVN	脆弱性	国内
JPCERT	インシデント	国内
IPA	脆弱性	国内
NVD API	脆弱性	海外
BleepingComputer	インシデント	海外
The Hacker News	ニュース	海外
Krebs on Security	ニュース	海外
CISA Alerts	脆弱性	海外
