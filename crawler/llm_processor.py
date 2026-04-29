import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

VALID_TAGS = [
    "vulnerability",
    "incident",
    "malware",
    "new-tech",
    "tool",
    "policy",
    "news",
]

PROMPT_TEMPLATE = """
以下のセキュリティ記事を分析して、JSON形式で返してください。

## 記事タイトル
{title}

## 記事本文（抜粋）
{body}

## 出力形式（必ずこのJSON形式のみで返すこと）
{{
  "summary_ja": "日本語で3〜5文の要約",
  "severity": "critical or high or medium or low or info",
  "cve_ids": ["CVE-XXXX-XXXX"],
  "tags": ["タグのslugを1〜3個選ぶ"]
}}

## タグの選択肢（slugで指定）
- vulnerability : 脆弱性情報、CVE、パッチ情報
- incident      : セキュリティインシデント、侵害、漏洩
- malware       : マルウェア、ランサムウェア、RAT
- new-tech      : 新技術、研究、新手法
- tool          : セキュリティツール、OSSリリース
- policy        : 政策、規制、ガイドライン
- news          : 一般的なセキュリティニュース

## 注意事項
- cve_idsはCVE番号が本文にない場合は空配列[]にする
- severityはCVSSスコアや影響度から判断。不明な場合はinfo
- JSON以外のテキストは一切出力しないこと
"""

def build_prompt(title: str, body: str) -> str:
    body_trimmed = body[:1000] if body else ""
    return PROMPT_TEMPLATE.format(title=title, body=body_trimmed)

def parse_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    return json.loads(text)

def process_article(title: str, body: str) -> dict:
    prompt = build_prompt(title, body)
    response = client.models.generate_content(
        model="gemma-4-26b-a4b-it",
        contents=prompt
    )
    result = parse_response(response.text)
    result["tags"] = [t for t in result.get("tags", []) if t in VALID_TAGS]
    return result

def get_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemma-4-26b-a4b-it")


def build_analysis_prompt(article: dict) -> str:
    title    = article.get("title", "")
    body     = (article.get("body_raw") or "")[:2000]
    summary  = article.get("summary_ja") or ""
    cve_ids  = ", ".join(article.get("cve_ids") or []) or "不明"
    cvss     = article.get("cvss_score") or "不明"
    severity = article.get("severity") or "不明"

    return f"""あなたはサイバーセキュリティの専門家です。
以下のセキュリティ情報について、詳細な分析レポートを日本語で作成してください。

## 情報
- タイトル: {title}
- CVE: {cve_ids}
- CVSS: {cvss}
- 深刻度: {severity}
- 要約: {summary}
- 本文: {body}

## 作成してほしいレポートの構成

### 🎯 この脆弱性・インシデントの概要
（何が問題か、影響を受けるシステムや環境を説明）

### 💀 攻撃者の視点：悪用シナリオ
（実際にどう悪用されうるか、ステップバイステップで説明。具体的な攻撃手法や悪用例があれば記載）

### 🛡 防御・対策方法
（具体的な対応策をリストアップ。パッチ適用、設定変更、代替手段など）

### ⚡ 緊急度と対応優先度
（CVSSスコア等を踏まえた判断基準と推奨アクション）

---
上記の構成でMarkdown形式の詳細レポートを作成してください。"""
