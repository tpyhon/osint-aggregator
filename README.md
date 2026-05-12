# 🛡 DeepMole — OSINT Security Aggregator

国内外のセキュリティ情報を自動収集・AI要約・分類するOSINTダッシュボードです。  
RSSとAPIで13ソースから記事を収集し、Google Gemini APIで日本語要約・タグ付け・詳細解析を行います。

---

## 機能

- 国内外のセキュリティ情報を **12時間ごとに自動収集**（GitHub Actions）
- LLMによる **日本語要約・深刻度判定・自動タグ付け**（Gemini API）
- 記事ごとの **詳細AI解析レポート**（概要・攻撃シナリオ・対策・優先度）
- 国内/海外・タグ・深刻度での **フィルタリング**
- キーワード・CVE番号での **全文検索**
- **ユーザー認証**（Supabase Auth）とユーザーごとの **ブックマーク管理**
- ブックマーク記事の **Notionエクスポート**
- Critical/High記事の **Slack即時通知**
- 5日以上前の記事を **自動削除**

---

## システム構成

```
[情報ソース] → [Crawler / GitHub Actions] → [Supabase PostgreSQL]
                                                      ↑
                                              [Gemini API（要約・解析）]
                                                      ↓
                                          [FastAPI / Render（バックエンド）]
                                                      ↓
                                          [Next.js / Vercel（フロントエンド）]
                                                      ↑
                                          [Supabase Auth（ユーザー認証）]
```

### インフラ構成（月額 $0）

| 役割 | 技術 | ホスティング |
|---|---|---|
| フロントエンド | Next.js / Tailwind CSS | Vercel（無料） |
| バックエンド | FastAPI / Python | Render（無料） |
| データベース | PostgreSQL | Supabase（無料） |
| 認証 | Supabase Auth | Supabase（無料） |
| クローラー | Python / GitHub Actions | GitHub Actions（無料） |
| LLM処理 | Google Gemini API / Gemma 4 26B | Google AI Studio（無料枠） |

---

## ディレクトリ構成

```
osint-aggregator/
├── .github/
│   └── workflows/
│       └── crawler.yml        # GitHub Actions（クロール・要約・解析）
├── crawler/
│   ├── main.py                # クローラーのエントリーポイント
│   ├── fetcher.py             # RSSフィード取得
│   ├── nvd_fetcher.py         # NVD API取得
│   ├── db.py                  # DB接続・操作
│   ├── llm_processor.py       # LLM要約・タグ付け・解析プロンプト
│   ├── summarizer.py          # 未処理記事のLLM要約処理
│   ├── summarize_all.py       # 要約バッチ処理ループ
│   ├── analyze_all.py         # AI詳細解析バッチ処理（新規）
│   ├── slack_notifier.py      # Slack通知
│   ├── notion_exporter.py     # Notionエクスポート
│   ├── cleanup.py             # 古い記事削除
│   └── .env                   # 環境変数（Git管理外）
├── backend/
│   ├── main.py                # FastAPI エンドポイント
│   ├── db.py                  # DB接続
│   └── .env                   # 環境変数（Git管理外）
├── frontend/
│   └── app/
│       ├── page.tsx           # メイン画面
│       ├── types.ts           # 型定義
│       ├── lib/
│       │   ├── api.ts         # APIクライアント（認証ヘッダー付き）
│       │   └── supabase.ts    # Supabaseクライアント
│       └── components/
│           ├── ArticleCard.tsx    # 記事カード
│           ├── AuthButton.tsx     # ログイン/ログアウトUI
│           └── SeverityBadge.tsx  # 深刻度バッジ
├── db/
│   └── init/
│       ├── 01_schema.sql      # DBスキーマ定義
│       └── 02_user_bookmarks.sql  # ユーザーブックマークテーブル
└── docker-compose.yml         # ローカル開発用PostgreSQL
```

---

## セットアップ（ローカル開発）

### 必要なもの

- Docker Desktop
- Python 3.11
- Node.js 18以上
- Gemini API キー（[Google AI Studio](https://aistudio.google.com/)）
- Supabase プロジェクト（[supabase.com](https://supabase.com/)）
- Slack Webhook URL（任意）
- Notion API キー（任意）

### 手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/tpyhon/osint-aggregator.git
cd osint-aggregator

# 2. ローカルDBを起動
docker compose up -d

# 3. Python環境を構築
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r crawler/requirements.txt
pip install -r backend/requirements.txt
pip install google-genai

# 4. 環境変数を設定
```

**`crawler/.env`**
```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=osint
DB_USER=osint_user
DB_PASSWORD=osint_pass
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemma-4-26b-a4b-it
SLACK_WEBHOOK_URL=your_slack_webhook_url   # 任意
NOTION_API_KEY=your_notion_api_key         # 任意
NOTION_DATABASE_ID=your_notion_database_id # 任意
```

**`backend/.env`**
```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=osint
DB_USER=osint_user
DB_PASSWORD=osint_pass
AUTH_REQUIRED=false
NOTION_API_KEY=your_notion_api_key         # 任意
NOTION_DATABASE_ID=your_notion_database_id # 任意
```

**`frontend/.env.local`**
```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
```

```bash
# 5. クローラーを実行
cd crawler
python main.py
python summarize_all.py
python analyze_all.py   # AI詳細解析（任意）

# 6. バックエンドを起動
cd backend
uvicorn main:app --reload --port 8000

# 7. フロントエンドを起動
cd frontend
npm install
npm run dev
# http://localhost:3000 にアクセス
```

---

## 本番デプロイ

### Supabase

1. SQLエディタで `db/init/01_schema.sql` と `db/init/02_user_bookmarks.sql` を実行
2. Authentication → Providers → Email を有効化
3. Authentication → URL Configuration で以下を設定:
   - Site URL: `https://osint-aggregator-tpyhons-projects.vercel.app`
   - Redirect URLs: `https://osint-aggregator-tpyhons-projects.vercel.app/**`

### Render（バックエンド）

| 環境変数 | 値 |
|---|---|
| `DB_HOST` | Supabase の DB ホスト |
| `DB_NAME` | `postgres` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | Supabase の DB パスワード |
| `AUTH_REQUIRED` | `true` |
| `SUPABASE_JWT_SECRET` | Supabase → Settings → JWT Keys → Legacy JWT Secret |
| `NOTION_API_KEY` | Notion API キー（任意） |
| `NOTION_DATABASE_ID` | Notion データベース ID（任意） |

ビルドコマンド:
```
pip install -r crawler/requirements.txt && pip install -r backend/requirements.txt
```

### Vercel（フロントエンド）

| 環境変数 | 値 |
|---|---|
| `NEXT_PUBLIC_API_BASE` | `https://deepmole-backend.onrender.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase → Settings → API Keys → Legacy anon key |

### GitHub Actions Secrets

| シークレット名 | 内容 |
|---|---|
| `DB_HOST` | Supabase の DB ホスト |
| `DB_PORT` | `5432` |
| `DB_NAME` | `postgres` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | Supabase の DB パスワード |
| `GEMINI_API_KEY` | Google AI Studio の API キー |
| `SLACK_WEBHOOK_URL` | Slack Webhook URL（任意） |

---

## 情報ソース

| ソース | 種別 | 地域 |
|---|---|---|
| JVN | 脆弱性 | 国内 |
| JPCERT | インシデント | 国内 |
| IPA | 脆弱性 | 国内 |
| NVD API | 脆弱性 | 海外 |
| BleepingComputer | インシデント | 海外 |
| The Hacker News | ニュース | 海外 |
| Krebs on Security | ニュース | 海外 |
| CISA Alerts | 脆弱性 | 海外 |

---

## 注意事項

- `SUPABASE_JWT_SECRET` はSupabaseの新しいECC署名形式に対応するため、署名検証をスキップしてissとexpのみ検証しています（`verify_signature: False`）。自前の認証基盤を使う場合は必ず署名検証を実装してください。
- Gemini API 無料枠はクラウドサーバー（Render等）のIPからアクセスするとブロックされる場合があります。LLM処理はGitHub Actionsから実行することで回避しています。
- Render 無料プランはアクセスがないと15分でスリープします。[UptimeRobot](https://uptimerobot.com/) 等で定期アクセスすることを推奨します。
