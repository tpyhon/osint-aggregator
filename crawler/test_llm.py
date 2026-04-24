from llm_processor import process_article

# テスト用記事
title = "CVE-2026-1234: Apache HTTP Server にリモートコード実行の脆弱性"
body = """
Apache HTTP Server 2.4.58以前のバージョンに重大な脆弱性が発見されました。
攻撃者はリモートから任意のコードを実行できる可能性があります。
CVSSスコアは9.8（Critical）で、早急なアップデートが推奨されています。
影響を受けるバージョンは2.4.0から2.4.58です。
"""

result = process_article(title, body)
print(result)
