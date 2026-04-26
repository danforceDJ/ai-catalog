# Contributing

Thanks for contributing to the AI catalog.

## Local development setup

Install the pre-commit hooks once per clone — they auto-regenerate `catalog.json` and `.github/plugin/marketplace.json` on every commit so you never have to remember to do it manually:

```bash
uv tool install pre-commit
pre-commit install
```

### Setting up a local virtual environment

For interactive troubleshooting — running scripts directly, debugging, or iterating quickly without the `uv run --script` overhead — create a venv with all dependencies in one step:

```bash
uv sync          # creates .venv/ and installs all deps (including pytest)
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

Once activated you can run scripts and tests directly:

```bash
python system/scripts/validate_catalog.py
python system/scripts/generate_catalog.py
pytest system/tests/
```

> **Note:** `.venv/` and `uv.lock` are git-ignored — do not commit them.

To run generators manually (outside of a commit):
```bash
uv run --script system/scripts/generate_catalog.py
uv run --script system/scripts/generate_marketplace.py
```

To validate the catalog without committing:
```bash
uv run --script system/scripts/validate_catalog.py
```

> **Note:** The regeneration hook runs against the full working tree, not just your staged files. If you use `git add -p` (partial staging), regenerate manually and stage the result before committing.

## Catalog layout

```
catalog/skills/<name>/SKILL.md          ← reusable skills
catalog/agents/<name>.agent.md          ← agent profiles
catalog/prompts/<name>.md               ← slash commands (filename stem must equal frontmatter name)
catalog/mcp/<name>/.mcp.json   ← MCP server configs
catalog/plugins/<name>/plugin.json      ← wrapper or bundle referencing primitives by name list
catalog/templates/<name>/TEMPLATE.md    ← raw-download-only templates
```

## Adding a standalone skill

1. Create `catalog/skills/<kebab-case-name>/SKILL.md` with frontmatter `name`, `description`, `version`.
   - **`name` must be the kebab-case slug** — matching the directory name (e.g. `jira-ticket-from-code`). Use the Markdown heading for the human-readable title.
2. Run `uv run --script system/scripts/validate_catalog.py` — fix any errors.
3. Regenerate artefacts and commit (see **Committing artefacts** below).

The skill appears in the web catalog with "Copy raw" and "Download zip" buttons. To make it installable via Copilot CLI, also create a plugin wrapper (see below).

## Adding a standalone agent

1. Create `catalog/agents/<kebab-case-name>.agent.md` with frontmatter `name`, `description`.
   - **`name` must be the kebab-case slug** — the same value as the filename stem (e.g. `senior-cloud-architect`), not a human-readable label. The human-readable title belongs in the Markdown heading inside the file body.
2. Validate, regenerate, commit.

## Adding a standalone command (slash command)

1. Create `catalog/prompts/<name>.md` with frontmatter `name`, `description`. **Filename stem must equal frontmatter `name`.**
2. Validate, regenerate, commit.

## Adding a standalone MCP server config

1. Create `catalog/mcp/<kebab-case-name>/.mcp.json` in the Copilot `{"servers": {...}}` shape.
2. Validate (secret scan runs automatically), regenerate, commit.

## Adding a plugin wrapper (single primitive, Copilot CLI installable)

1. Create `catalog/plugins/<name>/plugin.json` with a **name list** referencing your top-level primitive(s). Required field: `name` (must match directory name, kebab-case, ≤64 chars).
2. Reference the primitive by name:
   - **Skill** — `"skills": ["<name>"]` (resolves to `catalog/skills/<name>/SKILL.md`)
   - **Agent** — `"agents": ["<name>"]` (resolves to `catalog/agents/<name>.agent.md`)
   - **Command** — `"commands": ["<name>"]` (resolves to `catalog/prompts/<name>.md`)
   - **MCP** — `"mcpServers": ["<name>"]` (resolves to `catalog/mcp/<name>/.mcp.json`)
3. Regenerate marketplace metadata. This also materializes a Copilot-compatible plugin package at `catalog/plugins/<name>/.copilot-plugin/`.
4. Validate, regenerate, commit, and open a PR.

## Adding a bundle plugin

A bundle composes multiple primitives (≥2 component kinds) in a single installable plugin.

1. Create `catalog/plugins/<name>/plugin.json` with list-based references:

```json
{
  "name": "my-workflow-bundle",
  "description": "...",
  "version": "1.0.0",
  "category": "bundles",
  "skills": ["skill-a", "skill-b"],
  "mcpServers": ["my-mcp"]
}
```

2. Ensure all referenced primitives exist in their `catalog/` directories.
3. Validate, regenerate, commit, and open a PR.

## Adding a template (raw-download only)

1. Create `catalog/templates/<kebab-case-name>/TEMPLATE.md` with frontmatter `name`, `description`, `version`, `category`.
2. Optional supporting assets go alongside the `TEMPLATE.md`.
3. Validate, regenerate, and PR. Templates are NOT exposed to Copilot CLI; they appear in the web marketplace with download-only affordances.

## Testing the web UI locally

The `docs/` directory is git-ignored and built by CI — generate it locally to preview changes to the site template or catalog content:

```bash
# 1. Build the search index
uv run --script system/scripts/generate_catalog.py

# 2. Render docs/index.html
uv run --script system/scripts/generate_site.py

# 3. (Optional) Build downloadable zips — needed to test zip links
uv run --script system/scripts/generate_zips.py

# 4. Serve and open in your browser
python -m http.server 8000 --directory docs
# → http://localhost:8000
```

No extra dependencies are required beyond `uv` and Python 3.11+. Because the search index is embedded directly in `docs/index.html`, a plain file server is sufficient — no Node, no build step.

> **Note:** `docs/` is in `.gitignore`; never commit it. The deploy workflow regenerates it on merge to main.

## Committing artefacts

Stage your files and commit. If you installed the pre-commit hook (see **Local development setup** above), `system/artifacts/catalog.json` and `.github/plugin/marketplace.json` are regenerated and staged automatically. If you skipped hook setup, regenerate manually first:

```bash
uv run --script system/scripts/generate_catalog.py
uv run --script system/scripts/generate_marketplace.py
git add system/artifacts/catalog.json .github/plugin/marketplace.json
```

Open a PR. CI validates and checks that the tracked artefacts match the generated output; on merge the deploy workflow publishes `docs/` to GitHub Pages.

## Naming rules

- Kebab-case, ≤64 chars. Plugin directory name must match `plugin.json` `name`.
- **Frontmatter `name` in agent and skill files must be the kebab-case slug** (matching the filename stem / directory name), not a human-readable label. Put human-readable titles in the Markdown body heading.
- Command filenames must match their frontmatter `name`.
- No duplicate plugin names, command names, or embedded MCP server names across the catalog (enforced in CI).
- Sharing top-level MCP server configs across multiple bundles is intentional and allowed.

## Do not commit

- `docs/index.html`, `docs/catalog.json`, `docs/dl/*.zip` — these are generated by the deploy workflow and served via GitHub Pages; they are `.gitignore`d.

## Do commit

- `system/artifacts/catalog.json` and `.github/plugin/marketplace.json` — these are tracked artefacts required by Copilot CLI. Regenerate them locally and include in your PR (CI will fail if they are stale).

## Standards referenced

- Copilot CLI plugin spec — https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating
- Agent Skills — https://agentskills.io/
- AGENTS.md — https://agents.md/
- Model Context Protocol — https://modelcontextprotocol.io/
