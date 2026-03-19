# 2026-03-19 Notion read check and commit

- Branch: `fix/notion-mcp-enabled-tools`
- Request:
  - Notion が読めるか確認
  - このブランチの作業をコミット
- Summary:
  - Notion MCP の bot 情報取得で認証状態を確認
  - Notion 検索 API で実データ 1 件の読み取りを確認
  - 既存差分をコミット対象として整理
- Commands:
  - `git status -sb`
  - `git log --oneline --decorate -10`
  - `git diff -- .codex/config.toml`
  - `sed -n '1,220p' .codex/config.toml`
  - `sed -n '1,220p' logs/codex_sessions/20260319_0000_notion_mcp_config_fix.md`
