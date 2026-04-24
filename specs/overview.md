# Overview

## What This Project Is

A **company-wide, agent-agnostic AI configuration marketplace** that simultaneously serves as:

1. **A GitHub Copilot CLI Plugin Marketplace**
   - `copilot plugin marketplace add danforceDJ/ai-catalog`
   - Driven by `.github/plugin/marketplace.json`

2. **A Static Web Marketplace**
   - GitHub Pages site with live search, type filtering, and four install paths per card
   - Served from `docs/index.html`

Both outputs are **auto-generated** from a single filesystem source of truth.

## Standards Used

| Standard | Purpose |
|---|---|
| [AGENTS.md](https://agents.md/) | Agent behavior instruction files |
| [Agent Skills (agentskills.io)](https://agentskills.io/) | Reusable skill packages via `SKILL.md` |
| [Model Context Protocol](https://modelcontextprotocol.io/) | MCP server configuration via `.mcp.json` |
| [GitHub Copilot CLI plugin format](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) | Native install via `copilot plugin install` |

## Repository Layout

```
plugins/          — plugin wrappers/bundles (Copilot CLI installable)
skills/           — top-level reusable skill packages
agents/           — top-level agent behavior profiles
commands/         — top-level slash commands / prompts
mcpServers/       — top-level MCP server configs
templates/        — raw-download-only document templates
scripts/          — Python generation + validation scripts (PEP 723, run via uv)
catalog.json      — tracked search index (commit after every change)
.github/plugin/marketplace.json  — tracked Copilot CLI manifest (commit after every change)
docs/             — generated output (not committed, deployed via CI artifact)
specs/            — this specification folder
```

## Source Files vs. Generated Files

| File | Status | Owner |
|---|---|---|
| `catalog.json` | **Tracked in git** | Regenerate locally + commit with PRs |
| `.github/plugin/marketplace.json` | **Tracked in git** | Regenerate locally + commit with PRs |
| `docs/index.html` | Not committed | CI only (deploy workflow) |
| `docs/dl/*.zip` | Not committed | CI only |
| `docs/catalog.json` | Not committed | CI only |

→ See [`architecture.md`](architecture.md) for full data flow.
→ See [`catalog-contents.md`](catalog-contents.md) for what is currently in the catalog.

