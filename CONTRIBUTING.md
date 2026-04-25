# Contributing

Thanks for contributing to the AI catalog.

## Local development setup

Install the pre-commit hooks once per clone — they auto-regenerate `catalog.json` and `.github/plugin/marketplace.json` on every commit so you never have to remember to do it manually:

```bash
uv tool install pre-commit
pre-commit install
```

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

## Structure overview

The catalog lives under `catalog/`. Primitives are shareable across bundle plugins:

```
catalog/skills/<name>/SKILL.md          ← reusable standalone skills
catalog/agents/<name>.agent.md          ← standalone agent profiles
catalog/prompts/<name>.md               ← standalone slash commands (must match frontmatter name)
catalog/integrations/<name>/.mcp.json   ← standalone MCP server configs
catalog/plugins/<name>/plugin.json      ← wrapper (single primitive) or bundle (multiple primitives)
catalog/templates/<name>/TEMPLATE.md    ← raw-download-only document templates
```

Developer tooling lives under `system/`:
```
system/scripts/   ← generators, validators, install scripts
system/tests/     ← test suite
system/config/    ← marketplace.config.json
system/artifacts/ ← generated catalog.json, claude.marketplace.json
```

## Adding a standalone skill

1. Create `catalog/skills/<kebab-case-name>/SKILL.md` with frontmatter `name`, `description`, `version`.
2. Run `uv run --script system/scripts/validate_catalog.py` — fix any errors.
3. Regenerate artefacts and commit (see **Committing artefacts** below).

The skill appears in the web catalog with "Copy raw" and "Download zip" buttons. To make it installable via Copilot CLI, also create a plugin wrapper (see below).

## Adding a standalone agent

1. Create `catalog/agents/<kebab-case-name>.agent.md` with frontmatter `name`, `description`.
2. Validate, regenerate, commit.

## Adding a standalone command (slash command)

1. Create `catalog/prompts/<name>.md` with frontmatter `name`, `description`. **Filename stem must equal frontmatter `name`.**
2. Validate, regenerate, commit.

## Adding a standalone MCP server config

1. Create `catalog/integrations/<kebab-case-name>/.mcp.json` in the Copilot `{"servers": {...}}` shape.
2. Validate (secret scan runs automatically), regenerate, commit.

## Adding a plugin wrapper (single primitive, Copilot CLI installable)

1. Create `catalog/plugins/<name>/plugin.json` with a **name list** referencing your top-level primitive(s). Required field: `name` (must match directory name, kebab-case, ≤64 chars).
2. Reference the primitive by name:
   - **Skill** — `"skills": ["<name>"]` (resolves to `catalog/skills/<name>/SKILL.md`)
   - **Agent** — `"agents": ["<name>"]` (resolves to `catalog/agents/<name>.agent.md`)
   - **Command** — `"commands": ["<name>"]` (resolves to `catalog/prompts/<name>.md`)
   - **MCP** — `"mcpServers": ["<name>"]` (resolves to `catalog/integrations/<name>/.mcp.json`)
3. Regenerate marketplace metadata. This also materializes a Copilot-compatible plugin package at `catalog/plugins/<name>/.copilot-plugin/` (with generated `plugin.json`, copied primitive files, and generated `.mcp.json` when needed).
4. Validate, regenerate, commit, and open a PR.

> **Backward compatibility:** You may still embed content inside a plugin directory using string paths (`"skills": "skills"`, `"agents": "agents"`, etc.). This is supported but not recommended for new plugins — use top-level primitives for shareability.

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
