# Architecture

## Data Flow

```
Filesystem
  plugins/  +  skills/  +  agents/  +  commands/  +  mcpServers/  +  templates/
  marketplace.config.json
      │
      ▼
  generate_catalog.py          →  catalog.json  (tracked)
  generate_marketplace.py      →  .github/plugin/marketplace.json  (tracked)
                                   plugins/<name>/.copilot-plugin/  (generated package dirs)
      │
      ▼
  generate_site.py             →  docs/index.html  (not committed)
  generate_zips.py             →  docs/dl/<name>.zip  (not committed)
      │
      ▼
  GitHub Pages (web UI)  +  Copilot CLI (marketplace install)
```

## Two-Tier Content Model

### Tier 1 — Primitives (standalone, shareable)

Top-level directories. Discoverable by web UI. **Not** directly Copilot CLI installable unless wrapped in a plugin.

| Type | Path pattern | File |
|---|---|---|
| Skill | `skills/<name>/` | `SKILL.md` |
| Agent | `agents/` | `<name>.agent.md` |
| Command | `commands/` | `<name>.md` |
| MCP Server | `mcpServers/<name>/` | `.mcp.json` |
| Template | `templates/<name>/` | `TEMPLATE.md` |

### Tier 2 — Plugins (wrappers/bundles, Copilot CLI installable)

Every plugin lives under `plugins/<name>/` and has a `plugin.json` manifest. It wraps one or more primitives.

| Components found in `plugin.json` | Derived type |
|---|---|
| Only skills | `skill` |
| Only agents | `agent` |
| Only commands | `prompt` |
| Only MCP servers | `mcp` |
| ≥ 2 component kinds | `bundle` |
| None | `empty` |

## Plugin Reference Styles

`plugin.json` can reference primitives in two ways:

### List-reference (preferred for new plugins)

```json
{
  "skills": ["jira-ticket-from-code"],
  "mcpServers": ["atlassian"]
}
```

- Values are names of top-level primitives (e.g. `skills/jira-ticket-from-code/SKILL.md`)
- `generate_marketplace.py` materializes a `.copilot-plugin/` package directory by copying primitive files in
- The `source` path in `marketplace.json` points to `.copilot-plugin/`

### String-path (legacy, backward-compatible)

```json
{
  "skills": "skills",
  "mcpServers": ".mcp.json"
}
```

- Values are relative paths inside the plugin directory itself
- `source` in `marketplace.json` points to `plugins/<name>/` directly
- **Do not use for new plugins**

## `.copilot-plugin/` Package Generation

For list-reference plugins, `generate_marketplace.py`:

1. Clears and recreates `plugins/<name>/.copilot-plugin/`
2. Copies primitive files into it (`SKILL.md`, `*.agent.md`, `*.md`, `.mcp.json`)
3. Merges multiple MCP server configs into one `.mcp.json`
4. Writes a converted `plugin.json` (list refs → string paths)
5. Sets `source` in `marketplace.json` to `plugins/<name>/.copilot-plugin/`

## `marketplace.config.json`

Top-level metadata for the Copilot CLI marketplace manifest:

```json
{
  "name": "ai-catalog",
  "owner": "danforceDJ",
  "metadata": { ... }
}
```

