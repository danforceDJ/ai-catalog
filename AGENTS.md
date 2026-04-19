# Repository Agent Instructions

These instructions apply to agents working on this AI catalog repository.

## Scope

- Keep changes focused on catalog content (plugins, templates) and supporting scripts.
- Preserve Git-platform agnostic behavior (GitHub/GitLab compatible).

## Quality

- Follow existing naming conventions: lowercase, hyphen-separated names (kebab-case). Directory name must match `plugin.json` `name`.
- Validate before committing: `uv run --script scripts/validate_catalog.py`.
- Keep documentation accurate and synchronized with file structure.

## Security

- Never commit secrets, credentials, or tokens. `validate_catalog.py` scans `.mcp.json` files for common secret patterns.
- Prefer OAuth/SSO flows over static credentials where available.
- Do not hardcode internal-only endpoints unless explicitly required.

## Catalog Maintenance

- Add new plugins under `plugins/<name>/` with a `plugin.json` manifest.
  - Skills go under `plugins/<name>/skills/<skill-name>/SKILL.md`.
  - Agent profiles go under `plugins/<name>/agents/<agent-name>.agent.md`.
  - Prompts (slash commands) go under `plugins/<name>/commands/<command-name>.md`.
  - MCP configs go in `plugins/<name>/.mcp.json`.
- Add templates (raw-download-only) under `templates/<name>/TEMPLATE.md`.
- CI regenerates `catalog.json`, `.github/plugin/marketplace.json`, and `docs/` on merge to main — do not commit these artefacts manually.
