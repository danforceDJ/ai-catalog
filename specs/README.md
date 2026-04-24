# AI Catalog — Specification Index

> **For LLMs:** Read only the files relevant to your task. Each file is self-contained.
> Start here to find the right file, then load only that one.

## Quick Reference

| I need to know about… | Read |
|---|---|
| What this project is / high-level purpose | [`overview.md`](overview.md) |
| How data flows from files → Copilot CLI / web | [`architecture.md`](architecture.md) |
| Item types, their schemas, frontmatter fields | [`catalog-items.md`](catalog-items.md) |
| What content currently exists in the catalog | [`catalog-contents.md`](catalog-contents.md) |
| What each script does, inputs/outputs | [`scripts.md`](scripts.md) |
| How users install items (Copilot, VSCode, zip…) | [`install-paths.md`](install-paths.md) |
| Validation rules & secret scanning | [`validation-rules.md`](validation-rules.md) |
| CI/CD pipeline (GitHub Actions, GitLab, hooks) | [`cicd.md`](cicd.md) |
| Web UI layout, search, card features | [`web-ui.md`](web-ui.md) |
| Known bugs, gaps, and backlog | [`gaps.md`](gaps.md) |
| **Copilot CLI vs Claude Code vs VS Code — schemas, manifests, multi-platform strategy** | [`platform-comparison.md`](platform-comparison.md) |

## Naming Conventions (always apply)

- Plugin/primitive names: **kebab-case**, ≤ 64 chars, directory name **must** equal `plugin.json` `name`
- New primitives go at the **top level** (`skills/`, `agents/`, `commands/`, `mcpServers/`)
- Plugin wrappers/bundles go in `plugins/<name>/` with a `plugin.json` that references top-level primitive names

## Proposals & Design Decisions

| Proposal | Summary |
|---|---|
| [`../development/proposals/repo-structure-non-dev.md`](../development/proposals/repo-structure-non-dev.md) | Rename `commands/` → `prompts/`, `mcpServers/` → `tool-connections/`, `.mcp.json` → `connection.json`, `plugins/` → `packages/`; add per-directory READMEs and non-developer contribution guides |

## Key Commands (always run after changes)

```bash
uv run --script scripts/validate_catalog.py
uv run --script scripts/generate_catalog.py && uv run --script scripts/generate_marketplace.py
```

