# Catalog Item Types & Schemas

## Plugin (`plugins/<name>/plugin.json`)

Required for every plugin. Directory name **must** equal the `name` field.

### `plugin.json` Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | **Yes** | Kebab-case, ≤ 64 chars. Must equal directory name. |
| `description` | string | No | ≤ 1024 chars |
| `version` | string | No | Semver recommended |
| `author` | object | No | `{ name, email?, url? }` |
| `homepage` | string | No | |
| `repository` | string | No | |
| `license` | string | No | |
| `keywords` | array[string] | No | Used for web search |
| `category` | string | No | Used for display grouping |
| `tags` | array[string] | No | Used for display/search |
| `skills` | string \| array[string] | No | String = relative dir path (legacy). Array = list of top-level skill names. |
| `agents` | string \| array[string] | No | Same dual style as `skills` |
| `commands` | string \| array[string] | No | Same dual style as `skills` |
| `mcpServers` | string \| array[string] \| object | No | File path, list of top-level names, or inline config |
| `hooks` | string \| object | No | `hooks.json` path or inline (future type) |
| `lspServers` | string \| object | No | LSP server spec passthrough |

Schema: JSON Schema Draft 2020-12. Additional properties are allowed.

---

## Skill (`skills/<name>/SKILL.md`)

### YAML Frontmatter

| Field | Required | Notes |
|---|---|---|
| `name` | **Yes** | Should match folder name (mismatch = warning) |
| `description` | **Yes** | |
| `version` | No | Drift from `plugin.json` version = warning |
| `license` | No | |
| `compatibility` | No | Human-readable dependency note |
| `metadata` | No | Freeform object (`author`, `tags`, etc.) |

### Body Sections

```markdown
## Instructions
<step-by-step guidance for the AI agent>

## Example
<example input/output or usage>
```

---

## Agent (`agents/<name>.agent.md`)

### YAML Frontmatter

| Field | Required |
|---|---|
| `name` | **Yes** |
| `description` | **Yes** |

### Body

Markdown defining behavioral rules, git workflow, security policies, available tools/skills.

---

## Command / Slash Command (`commands/<name>.md`)

### YAML Frontmatter

| Field | Required | Notes |
|---|---|---|
| `name` | **Yes** | **Must equal the filename stem** (enforced by validator) |
| `description` | **Yes** | |

### Body

The prompt template text (the slash command content itself).

---

## MCP Server Config (`mcpServers/<name>/.mcp.json`)

```json
{
  "servers": {
    "<server-name>": {
      "type": "stdio",
      "command": "<executable>",
      "args": ["..."]
    }
  }
}
```

- Prefer OAuth / SSO flows — **never** hardcode tokens or credentials
- All `.mcp.json` files are secret-scanned on every validate + generate run (see [`validation-rules.md`](validation-rules.md))

---

## Template (`templates/<name>/TEMPLATE.md`)

### YAML Frontmatter

| Field | Required |
|---|---|
| `name` | **Yes** |
| `description` | **Yes** |
| `version` | **Yes** |
| `category` | **Yes** |
| `tags` | No |
| `keywords` | No |

Templates are **web-only** — no Copilot CLI install command is generated. Users can "Copy raw" or "Download zip" from the web UI.

