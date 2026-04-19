# AI Catalog

**🌐 Live Marketplace: [danforceDJ.github.io/ai-catalog](https://danforceDJ.github.io/ai-catalog/)**

A company-wide, agent-agnostic AI configuration marketplace built on three open standards plus the GitHub Copilot CLI plugin format:

- **[AGENTS.md](https://agents.md/)** for agent behavior instructions
- **[Agent Skills](https://agentskills.io/)** for reusable skill packages via `SKILL.md`
- **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)** for MCP server configurations
- **[GitHub Copilot CLI plugins](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating)** for native install via `copilot plugin install`

The repo is simultaneously a Copilot CLI plugin marketplace (via `.github/plugin/marketplace.json`) and a searchable web marketplace (GitHub Pages).

## Available Catalog Items

Four plugins + one template, all discoverable via the web marketplace or Copilot CLI:

| Type | Name | Description | Path |
|---|---|---|---|
| MCP | atlassian-mcp | Atlassian Rovo MCP via OAuth 2.1 | `plugins/atlassian-mcp/` |
| Skill | jira-ticket-from-code | Create Jira tickets from TODO/FIXME/BUG comments | `plugins/jira-ticket-from-code/` |
| Agent | default-agent | Company-wide default agent profile | `plugins/default-agent/` |
| Prompt | pr-description-prompt | Standard PR description command | `plugins/pr-description-prompt/` |
| Template | solution-architecture | Reusable Solution Architecture document | `templates/solution-architecture/` |

## Quick Start

### GitHub Copilot CLI (recommended)

```bash
copilot plugin marketplace add danforceDJ/ai-catalog
copilot plugin install jira-ticket-from-code@ai-catalog
copilot plugin install atlassian-mcp@ai-catalog
```

### Web marketplace

Open [danforceDJ.github.io/ai-catalog](https://danforceDJ.github.io/ai-catalog/). Per card you get:

- **Copilot install command** (copy button)
- **VSCode MCP deeplink** (MCP plugins only)
- **Copy raw file** (single-file skills/agents/prompts)
- **Download zip** (complete plugin bundle)

### Legacy `install.sh` (deprecated fallback)

```bash
./scripts/install.sh mcp atlassian-mcp --ide vscode --project /path/to/project
./scripts/install.sh skill jira-ticket-from-code --project /path/to/project
./scripts/install.sh agent default-agent --project /path/to/project
./scripts/install.sh prompt pr-description-prompt --project /path/to/project
./scripts/install.sh template solution-architecture --project /path/to/project
```

Prints a deprecation banner on every invocation — prefer the Copilot CLI flow above.

## IDE Notes

- **VSCode**: MCP configuration is merged into `.vscode/mcp.json`.
- **JetBrains IntelliJ**: MCP setup is manual in AI Assistant MCP settings; `install.sh` prints exact steps.

## Repository Structure

```text
.
├── .github/plugin/marketplace.json   # generated — Copilot CLI entry point
├── plugins/                           # source-of-truth plugins
│   ├── <name>/plugin.json
│   ├── <name>/skills/<skill-name>/SKILL.md
│   ├── <name>/agents/<agent-name>.agent.md
│   ├── <name>/commands/<command-name>.md
│   └── <name>/.mcp.json
├── templates/<name>/TEMPLATE.md       # raw-download-only templates
├── catalog.json                       # generated search index
├── docs/                              # generated static site (GitHub Pages)
│   ├── index.html
│   ├── catalog.json
│   └── dl/<name>.zip
└── scripts/                           # uv-run Python generators + bash fallback
    ├── generate_catalog.py
    ├── generate_marketplace.py
    ├── generate_zips.py
    ├── generate_site.py
    ├── validate_catalog.py
    └── install.sh                     # deprecated fallback
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) to add new plugins or templates.

## Marketplace

The static marketplace page at **[danforceDJ.github.io/ai-catalog](https://danforceDJ.github.io/ai-catalog/)** is auto-generated from `catalog.json` and published to GitHub Pages on every push to `main`.
