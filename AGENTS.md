# Repository Agent Instructions

These instructions apply to agents working on this AI catalog repository.

## Scope

- Keep changes focused on catalog content (`plugins/`, top-level primitives in `skills/`, `agents/`, `prompts/`, `mcp/`, `templates/`) and supporting scripts in `system/scripts/`.
- Preserve Git-platform agnostic behavior (GitHub/GitLab compatible).

## Quality

- Follow existing naming conventions: lowercase, hyphen-separated names (kebab-case). Directory name must match `plugin.json` `name`.
- Validate before committing: `uv run --script system/scripts/validate_catalog.py`.
- After adding or modifying plugins/templates or top-level primitives (`skills/`, `agents/`, `prompts/`, `mcp/`), regenerate tracked artefacts with the single convenience command: `uv run --script system/scripts/sync_catalog.py` (runs all four generators + validation in order). Alternatively run the generators individually: `uv run --script system/scripts/generate_catalog.py && uv run --script system/scripts/generate_marketplace.py && uv run --script system/scripts/generate_claude_marketplace.py && uv run --script system/scripts/generate_vscode_artifacts.py`.
- Commit regenerated artefacts alongside your changes: `system/artifacts/catalog.json`, `.github/plugin/marketplace.json`, `system/artifacts/claude.marketplace.json`, `.vscode/mcp.json`, `.github/prompts/*.prompt.md`, `.github/instructions/catalog-agent.instructions.md`, and generated plugin outputs under `plugins/*/` (`claude-plugin.json`, `.copilot-plugin/`, `.claude-plugin/`).
- Run the full test suite before committing: `uv run --with pytest --with pyyaml --with jsonschema --with jinja2 -- pytest -q system/tests/`.
- Keep documentation accurate and synchronized with file structure.

## Security

- Never commit secrets, credentials, or tokens. `validate_catalog.py` scans `.mcp.json` files for common secret patterns.
- Prefer OAuth/SSO flows over static credentials where available (for example, `plugins/atlassian-mcp/README.md` documents OAuth 2.1 SSO and no repository API tokens).
- Do not hardcode internal-only endpoints unless explicitly required.

## Catalog Maintenance

- Add standalone primitives under the root:
  - Skills go under `skills/<skill-name>/SKILL.md`.
  - Agent profiles go under `agents/<agent-name>.agent.md`.
  - Prompts (slash commands) go under `prompts/<command-name>.md`.
  - MCP configs go in `mcp/<name>/.mcp.json`.
- Add plugin wrappers/bundles under `plugins/<name>/` with a `plugin.json` manifest that references primitive names (for example: `"skills": ["jira-ticket-from-code"]`, `"mcpServers": ["atlassian"]`).
- Do not hand-edit generated compatibility outputs under plugin directories (`plugins/<name>/claude-plugin.json`, `plugins/<name>/.copilot-plugin/`, `plugins/<name>/.claude-plugin/`); regenerate them from source primitives and `plugin.json`.
- Add templates (raw-download-only) under `templates/<name>/TEMPLATE.md`.
- CI also regenerates `system/artifacts/catalog.json`, `.github/plugin/marketplace.json`, and `docs/` on merge to main. For PRs, regenerate and commit tracked generator outputs with your changes (`system/artifacts/catalog.json`, `.github/plugin/marketplace.json`, `system/artifacts/claude.marketplace.json`, `.vscode/mcp.json`, `.github/prompts/*.prompt.md`, `.github/instructions/catalog-agent.instructions.md`, and generated plugin compatibility files under `plugins/*/`); `docs/` remains CI-managed.
