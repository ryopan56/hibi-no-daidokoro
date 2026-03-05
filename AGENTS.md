# AGENTS.md (hibi-no-daidokoro)
目的: 「日々の台所」プロジェクトの前提・運用ルールをCodexに伝える。

## 技術スタック / 前提
- Django 5.x
- PostgreSQL
- Docker Compose 前提
- Django Templates
- ログ: logs/app/
- セッションログ: logs/codex_sessions/（Git管理対象）

## Git運用方針（重要）
- main は常に安定
- タスクごとにブランチ運用（feat/task-xx）
- 回収・整理は chore ブランチで行う
- commit と push はローカル git を使う
- Pull Request の作成・更新のみ、承認済み GitHub MCP 経由で行ってよい

## 外部接続方針
- Codex本体の一般ネットワークアクセスは原則使わない。
- 外部参照や GitHub 操作が必要な場合は、承認済みMCP経由に限定する。
- このプロジェクトでは GitHub MCP を Pull Request 作成・更新用途にのみ許可する。
- 承認されていない外部サイト/APIへの接続は行わない。必要ならユーザーに相談して止める。

## 秘密情報
- APIキー/トークン/パスワード/秘密鍵/.env 実値は参照・出力しない。
- `.env` は開かない（変数名の話のみ可、値は不可）。

## 変更の境界（守ること）
- 指定がない限り、変更範囲はタスクに関連するアプリ/テンプレートに限定する。
- settings/urls など横展開の変更は必要性を先に説明してから。

## ローカル生成物の扱い
- *.log, media/, __pycache__/ 等はGit管理しない
- .env はGit管理しない（.env.example のみ）

## テスト / 検証
- 変更後は原則テストを実行する:
  - python manage.py test

## 報告
完了時に必ず含める:
1. 変更ファイル
2. 変更概要
3. 実行コマンド（テスト含む）
4. 注意点 / 残課題
