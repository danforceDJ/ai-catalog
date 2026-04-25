# Known Gaps & Backlog

> Priority: **P1** = blocks correctness / install reliability. **P2** = UX / developer experience.

---

## P1 — Correctness & Reliability

### No `type` field in `plugin.json`
- Type is only inferred at generate time by `derive_type()`
- A typo in a component reference silently produces `type: "empty"` with no validation error
- **Fix:** Add a `type` enum to the JSON Schema and enforce it in `validate_catalog.py`

### SKILL.md `name` drift is warning-only
- If `name` in frontmatter doesn't match the folder name, Copilot installs the skill under the wrong name
- **Fix:** Promote to an **error** in `validate_catalog.py`

### `install.sh` stale paths for all current plugins
- `install.sh` reads skills/agents/commands from `plugins/<name>/skills/<name>/`, `plugins/<name>/agents/`, etc.
- All 5 current plugins use list-reference style — those embedded sub-paths don't exist
- Any `skill | agent | prompt` install via `install.sh` would fail at runtime
- **Fix:** Update `install.sh` to read from top-level primitives, or remove the code paths entirely (since it's deprecated)

### `atlassian` standalone catalog entry duplicates `atlassian-mcp`
- `mcpServers/atlassian/` emits a standalone entry with empty metadata (no description, version, category)
- Creates a confusing duplicate card in the web UI alongside the `atlassian-mcp` plugin card
- **Fix:** Either add metadata to `mcpServers/atlassian/.mcp.json` or improve the deduplication logic in `generate_catalog.py`

### Missing `instructions/` content type
- `.instructions.md` files with `applyTo` frontmatter (auto-applied coding standards) are not supported
- Highest business-value missing content type for dev productivity
- **Fix:** Add discovery, validation, schema, and install handling for an `instructions` type

---

## P2 — Developer Experience & UX

### No scaffolding script
- Contributors must hand-write all `plugin.json`, SKILL.md, agent.md, etc. boilerplate
- **Fix:** Add `scripts/scaffold_plugin.py` CLI

### No `llms.txt`
- AI agents cannot programmatically discover the catalog or its conventions
- **Fix:** Generate a `docs/llms.txt` from the catalog

### Web UI lacks category/tag filtering
- Only type-tab filtering exists; no way to filter by `category` or `tags`
- **Fix:** Add filter controls to `scripts/templates/index.html.j2`

### Zips include generated `.copilot-plugin/` directories
- `generate_zips.py` zips `plugins/<name>/` recursively with no exclude list
- Download ZIPs contain internal generated artifacts
- **Fix:** Add an exclude pattern for `.copilot-plugin/` in `zip_directory()`

### No `hooks/` content type implementation
- `hooks` is listed in `PLUGIN_SCHEMA` and passed through in `generate_marketplace.py`
- No discovery, validation, or web UI handling exists
- **Fix:** Implement discovery + validation for `hooks.json`

### `score_item()` in `generate_site.py` is dead code in production
- Python scoring function is only used in tests for JS parity checking
- Not called at render time; scoring happens entirely client-side
- Low priority — harmless, but confusing

### No VSCode deeplinks for non-MCP types
- Deeplinks are only generated for MCP server installs
- Agent, skill, and prompt types have no equivalent one-click VSCode install
- **Fix:** Investigate VSCode extension APIs for agent/skill installation deeplinks

---

## Content Gaps

The catalog is currently Atlassian-focused only. Likely additions:
- GitHub MCP server (Copilot-native `github.copilot.chat.mcp.enabled` config)
- Slack / Teams MCP integration
- Coding standards / linting instructions (once `instructions/` type is added)
- Code review agent profile
- More document templates

