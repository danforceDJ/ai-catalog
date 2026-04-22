# Repository Agent Instructions

These instructions apply to agents working on this AI catalog repository.

## Scope

- Keep changes focused on catalog content (`plugins/`, top-level primitives in `skills/`, `agents/`, `commands/`, `mcpServers/`, `templates/`) and supporting scripts.
- Preserve Git-platform agnostic behavior (GitHub/GitLab compatible).

## Quality

- Follow existing naming conventions: lowercase, hyphen-separated names (kebab-case). Directory name must match `plugin.json` `name`.
- Validate before committing: `uv run --script scripts/validate_catalog.py`.
- After adding or modifying plugins/templates or top-level primitives (`skills/`, `agents/`, `commands/`, `mcpServers/`), regenerate tracked artefacts: `uv run --script scripts/generate_catalog.py && uv run --script scripts/generate_marketplace.py`. Commit `catalog.json` and `.github/plugin/marketplace.json` alongside your changes.
- Keep documentation accurate and synchronized with file structure.

## Security

- Never commit secrets, credentials, or tokens. `validate_catalog.py` scans `.mcp.json` files for common secret patterns.
- Prefer OAuth/SSO flows over static credentials where available.
- Do not hardcode internal-only endpoints unless explicitly required.

## Catalog Maintenance

- Add standalone primitives at the top level:
  - Skills go under `skills/<skill-name>/SKILL.md`.
  - Agent profiles go under `agents/<agent-name>.agent.md`.
  - Prompts (slash commands) go under `commands/<command-name>.md`.
  - MCP configs go in `mcpServers/<name>/.mcp.json`.
- Add plugin wrappers/bundles under `plugins/<name>/` with a `plugin.json` manifest that references primitive names (for example: `"skills": ["jira-ticket-from-code"]`, `"mcpServers": ["atlassian"]`).
- Nested component paths under `plugins/<name>/...` are legacy compatibility paths; do not use them for new catalog content.
- Add templates (raw-download-only) under `templates/<name>/TEMPLATE.md`.
- CI also regenerates `catalog.json`, `.github/plugin/marketplace.json`, and `docs/` on merge to main. For PRs, regenerate and commit the tracked artefacts (`catalog.json` and `.github/plugin/marketplace.json`) with your changes; `docs/` remains CI-managed.
