# Contributing

Thanks for contributing to the AI catalog.

## Adding a new plugin

1. Create `plugins/<kebab-case-name>/plugin.json`. Required field: `name` (must match the directory name, kebab-case, ≤64 chars). Recommended: `description`, `version`, `author`, `keywords`, `category`, `tags`.
2. Add the component(s) your plugin ships:
   - **Skill** — `skills/<skill-name>/SKILL.md` with frontmatter `name`, `description`, `version`.
   - **Agent** — `agents/<agent-name>.agent.md` with frontmatter `name`, `description`.
   - **Prompt (command)** — `commands/<command-name>.md` with frontmatter `name`, `description`. **Filename stem must equal `name`.**
   - **MCP** — `.mcp.json` in the Copilot `{"servers": {...}}` shape.
3. Declare the component path(s) in `plugin.json` (`skills`, `agents`, `commands`, `mcpServers`). Defaults are `skills/`, `agents/`, `commands/`, `.mcp.json`.
4. Run `uv run --script scripts/validate_catalog.py` locally — fix any errors.
5. Regenerate tracked artefacts and commit them:
   ```bash
   uv run --script scripts/generate_catalog.py
   uv run --script scripts/generate_marketplace.py
   git add catalog.json .github/plugin/marketplace.json
   git commit -m "chore: regenerate catalog"
   ```
6. Open a PR. CI validates and checks that the tracked artefacts match the generated output; on merge the deploy workflow publishes `docs/` to GitHub Pages.

## Adding a template (raw-download only)

1. Create `templates/<kebab-case-name>/TEMPLATE.md` with frontmatter `name`, `description`, `version`, `category`.
2. Optional supporting assets go alongside the `TEMPLATE.md`.
3. Run validation, regenerate artefacts, and PR as above. Templates are NOT exposed to Copilot CLI; they appear in the web marketplace with download-only affordances.

## Creating a bundle plugin

A bundle is a plugin that ships ≥2 component kinds (e.g. skill + MCP). Same authoring flow as above; declare every component path in `plugin.json`. Name it `<theme>-workflow` or similar for clarity.

## Naming rules

- Kebab-case, ≤64 chars. Directory name must match `plugin.json` `name`.
- Command filenames must match their frontmatter `name`.
- No duplicate plugin names, command names, or MCP server names across the catalog (enforced in CI).

## Do not commit

- `catalog.json`, `.github/plugin/marketplace.json`, `docs/index.html`, `docs/catalog.json`, `docs/dl/*.zip` — CI owns these files. They are `.gitignore`d locally; the deploy workflow `git add -f`s them on push to main.

## Standards referenced

- Copilot CLI plugin spec — https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating
- Agent Skills — https://agentskills.io/
- AGENTS.md — https://agents.md/
- Model Context Protocol — https://modelcontextprotocol.io/
