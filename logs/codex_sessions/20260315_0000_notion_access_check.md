# 2026-03-15 Notion access check

## Request
- Verify whether a Notion page can be read
- Verify that writing is not technically available
- Do not perform any other operation

## Commands / Checks
- `list_mcp_resources`
- `list_mcp_resource_templates`
- `rg -n "notion|Notion|read-only|readonly|capabilit|mcp" .codex/config.toml`
- `sed -n '28,52p' .codex/config.toml`
- `rg --files logs/codex_sessions`
- `git status -sb`
- `git log --oneline --decorate -10`

## Findings
- MCP resource listing returned no exposed resources and no resource templates.
- `.codex/config.toml` defines `[mcp_servers.notion]` as `Notion MCP (local / read-only token)`.
- Enabled Notion tools are limited to search/query/retrieve/get operations.
- No create/update/append/delete style Notion operations are enabled in the config.

## Conclusion
- From configuration, read-side Notion access is intended.
- In this session, no Notion resource was exposed through MCP resource listing, so an actual page read could not be exercised here.
- Write operations are not technically available from the configured Notion MCP tool set.
