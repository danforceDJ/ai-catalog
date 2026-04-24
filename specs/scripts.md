# Scripts

All scripts are **PEP 723 single-file Python scripts** (Python ≥ 3.11). Run via `uv run --script scripts/<name>.py`. No `requirements.txt` needed — dependencies are declared inline.

---

## `generate_catalog.py`

**Purpose:** Build `catalog.json` (search index) from the filesystem.

**Dependencies:** `pyyaml>=6`

**Inputs:**
- `plugins/*/plugin.json`
- `skills/*/SKILL.md`
- `agents/*.agent.md`
- `commands/*.md`
- `mcpServers/*/.mcp.json`
- `templates/*/TEMPLATE.md`

**Outputs:** `catalog.json` + `docs/catalog.json` (copy for the site)

**Key logic:**
1. Scans `plugins/` alphabetically; resolves both list-ref and string-path component styles
2. `derive_type()` → infers `skill | agent | prompt | mcp | bundle | empty` from components found
3. `build_deeplink()` → generates `vscode:mcp/install?name=...&config=<base64url>` for MCP plugins (capped at 2048 bytes)
4. `raw_files()` → returns single raw file path for single-primitive string-path plugins only
5. Collects covered primitive names; top-level primitives **not covered** by any plugin get standalone entries (with `copilot: null`)
6. Scans `templates/` via frontmatter

**Output schema per entry:**

```json
{
  "name": "...",
  "description": "...",
  "version": "...",
  "type": "skill|agent|prompt|mcp|bundle|template|empty",
  "category": "...",
  "tags": [],
  "keywords": [],
  "components": {
    "skills": [], "agents": [], "commands": [], "mcpServers": [], "hooks": false
  },
  "install": {
    "copilot": "<name>@ai-catalog | null",
    "vscodeMcpDeeplink": "vscode:mcp/install?... | null",
    "rawFiles": [],
    "zip": "dl/<name>.zip",
    "repoPath": "plugins/<name> | skills/<name> | ..."
  }
}
```

---

## `generate_marketplace.py`

**Purpose:** Build `.github/plugin/marketplace.json` (Copilot CLI manifest) and materialize `.copilot-plugin/` packages.

**Dependencies:** stdlib only

**Inputs:** `plugins/*/plugin.json`, `marketplace.config.json`, top-level primitive files

**Outputs:**
- `.github/plugin/marketplace.json`
- `plugins/<name>/.copilot-plugin/` (generated package dir, one per list-reference plugin)

**Key logic:**
- For **list-reference plugins**: creates `.copilot-plugin/`, copies primitive files in, merges MCP configs, converts list refs → string paths in the output `plugin.json`. Sets `source` to `.copilot-plugin/`.
- For **string-path plugins**: `source` is `plugins/<name>/` directly.
- `PASSTHROUGH_FIELDS` copied verbatim: `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `category`, `tags`, `skills`, `agents`, `commands`, `hooks`, `lspServers`

---

## `generate_site.py`

**Purpose:** Render `docs/index.html` from `catalog.json` + Jinja2 template.

**Dependencies:** `jinja2>=3`

**Inputs:** `catalog.json`, `scripts/templates/index.html.j2`

**Output:** `docs/index.html`

**Key logic:**
- Renders with: `generated_at` (UTC ISO 8601), `repo_url`, `repo_url_json`, `catalog_json` (entire JSON inlined as JS constant)
- Contains a Python `score_item()` function — only used by tests for parity checking against the JavaScript scoring; not called at render time.

---

## `generate_zips.py`

**Purpose:** Produce `docs/dl/<name>.zip` for every plugin and template.

**Dependencies:** stdlib only

**Inputs:** `plugins/*/`, `templates/*/`

**Output:** `docs/dl/<name>.zip` (created; warns if > 1 MB)

**Known issue:** Zips the entire plugin directory including generated `.copilot-plugin/` sub-directories. No exclude filter.

---

## `validate_catalog.py`

**Purpose:** Validate the entire catalog. Exit 1 on any error; warnings to stderr only.

**Dependencies:** `pyyaml>=6`, `jsonschema>=4`

**What it validates:** See [`validation-rules.md`](validation-rules.md) for the full rule set.

---

## `install.sh`

**Status: DEPRECATED.** Prints a deprecation banner on every invocation directing users to `copilot plugin install`.

**Supported types:** `mcp | skill | agent | prompt | template`

**Known issue:** Reads skills/agents/commands from **embedded plugin sub-paths** (`plugins/<name>/skills/<name>/`, etc.) — these paths don't exist for any current list-reference plugin. Would fail at runtime for all 5 current plugins when used for `skill`, `agent`, or `prompt` types.

**Options:** `--ide vscode|jetbrains`, `--project <path>`, `--global`

