# Repository Agent Instructions

These instructions apply to agents working on this AI catalog repository.

## Scope

- Keep changes focused on catalog content and supporting scripts.
- Preserve Git-platform agnostic behavior (GitHub/GitLab compatible).

## Quality

- Follow existing naming conventions: lowercase, hyphen-separated names.
- Validate shell scripts before committing.
- Keep documentation accurate and synchronized with file structure.

## Security

- Never commit secrets, credentials, or tokens.
- Prefer OAuth/SSO flows over static credentials where available.
- Do not hardcode internal-only endpoints unless explicitly required.

## Catalog Maintenance

- Add MCP servers under `mcp/<name>/`.
- Add skills under `skills/<name>/SKILL.md`.
- Add agent profiles under `agents/<name>/AGENTS.md`.
- Regenerate `catalog.json` with `./scripts/generate-catalog.sh` after updates.
