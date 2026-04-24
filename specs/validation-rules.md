# Validation Rules

`validate_catalog.py` — exit code 1 on any **Error**; **Warnings** go to stderr only (exit 0).

---

## Plugin-Level Rules (per `plugins/<name>/`)

| Rule | Level |
|---|---|
| `plugin.json` exists | Error |
| `plugin.json` is valid JSON | Error |
| Passes JSON Schema (Draft 2020-12) | Error |
| `name` matches regex `^[a-z0-9]+(?:-[a-z0-9]+)*$`, ≤ 64 chars | Error |
| `name` == directory name | Error |
| For list-ref skills: `skills/<name>/SKILL.md` exists | Error |
| For list-ref agents: `agents/<name>.agent.md` exists | Error |
| For list-ref commands: `commands/<name>.md` exists | Error |
| For list-ref mcpServers: `mcpServers/<name>/.mcp.json` exists | Error |
| String-path `skills` dir has ≥ 1 `SKILL.md` | Error |
| String-path `agents` dir has ≥ 1 `*.agent.md` | Error |
| String-path `commands` dir has ≥ 1 `*.md` | Error |
| Command `.md` frontmatter has `name` and `description` | Error |
| Command frontmatter `name` == filename stem | Error |
| SKILL.md `version` matches `plugin.json` `version` | **Warning** |

---

## Global Uniqueness Rules

| Rule | Level |
|---|---|
| No duplicate plugin `name` across `plugins/` | Error |
| No duplicate command filename stem across all plugin command dirs | Error |
| No duplicate MCP server name across string-path `.mcp.json` files | Error |

> List-based MCP refs intentionally share top-level configs — sharing is allowed and skips the uniqueness check.

---

## Marketplace File Rules

| Rule | Level |
|---|---|
| `.github/plugin/marketplace.json` is valid JSON | Error |
| Passes JSON Schema (`MARKETPLACE_SCHEMA`) | Error |
| Each plugin `source` path exists as a directory | Error |

---

## Template Rules (per `templates/<name>/`)

| Rule | Level |
|---|---|
| `TEMPLATE.md` exists | Error |
| Frontmatter has `name` | Error |
| Frontmatter has `description` | Error |
| Frontmatter has `version` | Error |
| Frontmatter has `category` | Error |

---

## Standalone Primitive Rules

| Primitive | Rules checked |
|---|---|
| `skills/<name>/SKILL.md` | File exists; frontmatter `name` present; frontmatter `description` present |
| `agents/<name>.agent.md` | Frontmatter `name` present; frontmatter `description` present |
| `commands/<name>.md` | Frontmatter `name` and `description` present; `name` == filename stem |
| `mcpServers/<name>/.mcp.json` | File exists; valid JSON; secret scan |

---

## Secret Scan Patterns

Applied to **every** `.mcp.json` file (plugin-level and top-level) on both validate and generate runs:

| Pattern | Catches |
|---|---|
| `\b(password\|passwd\|secret\|api[_-]?key\|api[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}` | Generic credential assignments |
| `ghp_[A-Za-z0-9]{36}` | GitHub classic personal access token |
| `gho_[A-Za-z0-9]{36}` | GitHub OAuth token |
| `ghu_[A-Za-z0-9]{36}` | GitHub user-to-server token |
| `"API_TOKEN"\s*:\s*"[^"]{8,}"` | JSON `API_TOKEN` literal |

