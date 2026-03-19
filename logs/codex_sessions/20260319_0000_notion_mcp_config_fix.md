# 2026-03-19 Notion MCP config fix

- Branch: `fix/notion-mcp-enabled-tools`
- Request: `.codex/config.toml` の Notion `enabled_tools` から不要と思われる `mcp__notion__` 接頭辞を削除
- Changed file: `.codex/config.toml`
- Summary:
  - `enabled_tools` 内の Notion ツール名を `API-*` 形式へ修正
  - その他の設定値は変更なし
- Commands:
  - `git status -sb`
  - `git log --oneline --decorate -10`
  - `git checkout -b fix/notion-mcp-enabled-tools`
  - `git diff -- .codex/config.toml`
