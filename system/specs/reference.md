# Catalog Reference

## Item Schemas

### Plugin (`catalog/plugins/<name>/plugin.json`)

Directory name must equal the `name` field.

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | **Yes** | Kebab-case, ≤ 64 chars, equals directory name |
| `description` | string | No | ≤ 1024 chars |
| `version` | string | No | Semver recommended |
| `category` | string | No | Display grouping |
| `tags` / `keywords` | array[string] | No | Search/display |
| `skills` | string \| array[string] | No | Array = list of top-level skill names (preferred) |
| `agents` | string \| array[string] | No | Same as `skills` |
| `commands` | string \| array[string] | No | Same as `skills` |
| `mcpServers` | string \| array[string] | No | Array = top-level integration names (preferred) |

### Skill (`catalog/skills/<name>/SKILL.md`)

YAML frontmatter:

| Field | Required |
|---|---|
| `name` | **Yes** — should match folder name (mismatch = warning) |
| `description` | **Yes** |
| `version` | No — drift from `plugin.json` version = warning |

Body: `## Instructions` and optional `## Example` sections.

### Agent (`catalog/agents/<name>.agent.md`)

Frontmatter: `name` (**required**), `description` (**required**). Body: behavioral rules in Markdown.

### Command / Slash Command (`catalog/prompts/<name>.md`)

Frontmatter: `name` (**required**, **must equal the filename stem**), `description` (**required**). Body: prompt template text.

### MCP Server Config (`catalog/mcp/<name>/.mcp.json`)

```json
{
  "servers": {
    "<server-name>": { "type": "stdio", "command": "<executable>", "args": ["..."] }
  }
}
```

Never hardcode credentials. All `.mcp.json` files are secret-scanned on every validate/generate run.

### Template (`catalog/templates/<name>/TEMPLATE.md`)

Frontmatter: `name`, `description`, `version`, `category` — all **required**. Templates are web-only (no Copilot CLI install).

---

## Validation Rules

`validate_catalog.py` — exits 1 on **Error**, warnings go to stderr (exit 0).

### Plugin rules

| Rule | Level |
|---|---|
| `plugin.json` exists, is valid JSON, passes schema | Error |
| `name` is kebab-case, ≤ 64 chars, equals directory name | Error |
| Each listed primitive (`skills`, `agents`, `commands`, `mcpServers`) exists at its path | Error |
| Command frontmatter `name` == filename stem | Error |
| SKILL.md `version` matches `plugin.json` `version` | Warning |

### Global uniqueness

| Rule | Level |
|---|---|
| No duplicate plugin `name` across `catalog/plugins/` | Error |
| No duplicate command filename stem across all plugin command dirs | Error |
| No duplicate MCP server name (string-path only; list refs may share top-level configs) | Error |

### Template rules

Frontmatter must have `name`, `description`, `version`, `category` — all Error if missing.

### Secret scan patterns (applied to every `.mcp.json`)

| Pattern | Catches |
|---|---|
| `password|passwd|secret|api[_-]?key` followed by `=` or `:` and a value ≥ 8 chars | Generic credentials |
| `ghp_[A-Za-z0-9]{36}` | GitHub classic PAT |
| `gho_[A-Za-z0-9]{36}` | GitHub OAuth token |
| `"API_TOKEN": "<value ≥ 8 chars>"` | JSON API_TOKEN literal |

---

## Install Paths

| Method | Available for | How |
|---|---|---|
| **Copilot CLI** | All 5 plugins | `copilot plugin install <name>@ai-catalog` |
| **VSCode MCP deeplink** | MCP plugins where config ≤ 2 KB | `vscode:mcp/install?<url-encoded-json>` where JSON = `{"name":"…",…serverConfig}` |
| **Copy raw** | Single-file primitives and templates | Web modal fetches from `raw.githubusercontent.com` |
| **Download zip** | All plugins and templates | `docs/dl/<name>.zip` |

### Matrix

| Type | Copilot CLI | VSCode deeplink | Copy raw | Zip |
|---|---|---|---|---|
| Plugin (mcp) | ✅ | ✅ if ≤ 2 KB | ❌ | ✅ |
| Plugin (skill/agent/prompt) | ✅ | ❌ | ✅ | ✅ |
| Plugin (bundle) | ✅ | ✅ if has MCP ≤ 2 KB | ❌ | ✅ |
| Standalone primitive | ❌ | ❌ | ✅ | ❌ |
| Template | ❌ | ❌ | ✅ | ✅ |
