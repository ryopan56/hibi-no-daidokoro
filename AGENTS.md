# hibi-no-daidokoro プロジェクト指針

## 技術前提
- Django 5.x / PostgreSQL / Docker Compose / Django Templates
- logs/app, logs/codex_sessions を運用（後者はGit管理対象）

## Git運用
- main は常に安定
- タスクごとにブランチ（feat/task-xx）
- push はユーザーがローカルで実施
- PR作成/更新のみ GitHub MCP 経由で可（ユーザー明示指示があるときだけ）

## 外部接続
- Codex本体のネットは原則OFF
- GitHub操作は GitHub MCP（PR作成/更新）に限定
- それ以外の外部接続は実施しない（必要なら止めて相談）

## テスト
- 変更後は `docker compose exec web python manage.py test` を基本
