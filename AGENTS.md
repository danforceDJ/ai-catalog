# Repository Agent Instructions

These instructions apply to agents working on this AI catalog repository.

## Scope

- Keep changes focused on catalog content (`catalog/plugins/`, top-level primitives in `catalog/skills/`, `catalog/agents/`, `catalog/prompts/`, `catalog/integrations/`, `catalog/templates/`) and supporting scripts in `system/scripts/`.
- Preserve Git-platform agnostic behavior (GitHub/GitLab compatible).

## Quality

- Follow existing naming conventions: lowercase, hyphen-separated names (kebab-case). Directory name must match `plugin.json` `name`.
- Validate before committing: `uv run --script system/scripts/validate_catalog.py`.
- After adding or modifying plugins/templates or top-level primitives (`catalog/skills/`, `catalog/agents/`, `catalog/prompts/`, `catalog/integrations/`), regenerate tracked artefacts: `uv run --script system/scripts/generate_catalog.py && uv run --script system/scripts/generate_marketplace.py`. Commit `system/artifacts/catalog.json` and `.github/plugin/marketplace.json` alongside your changes.
- Keep documentation accurate and synchronized with file structure.

## Security

- Never commit secrets, credentials, or tokens. `validate_catalog.py` scans `.mcp.json` files for common secret patterns.
- Prefer OAuth/SSO flows over static credentials where available.
- Do not hardcode internal-only endpoints unless explicitly required.

## Catalog Maintenance

- Add standalone primitives under `catalog/`:
  - Skills go under `catalog/skills/<skill-name>/SKILL.md`.
  - Agent profiles go under `catalog/agents/<agent-name>.agent.md`.
  - Prompts (slash commands) go under `catalog/prompts/<command-name>.md`.
  - MCP configs go in `catalog/integrations/<name>/.mcp.json`.
- Add plugin wrappers/bundles under `catalog/plugins/<name>/` with a `plugin.json` manifest that references primitive names (for example: `"skills": ["jira-ticket-from-code"]`, `"mcpServers": ["atlassian"]`).
- Nested component paths under `catalog/plugins/<name>/...` are legacy compatibility paths; do not use them for new catalog content.
- Add templates (raw-download-only) under `catalog/templates/<name>/TEMPLATE.md`.
- CI also regenerates `system/artifacts/catalog.json`, `.github/plugin/marketplace.json`, and `docs/` on merge to main. For PRs, regenerate and commit the tracked artefacts (`system/artifacts/catalog.json` and `.github/plugin/marketplace.json`) with your changes; `docs/` remains CI-managed.
