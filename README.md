# AI Catalog

**🌐 Live Marketplace: [danforceDJ.github.io/ai-catalog](https://danforceDJ.github.io/ai-catalog/)**

A company-wide, agent-agnostic AI configuration marketplace built on three open standards plus the GitHub Copilot CLI plugin format:

- **[AGENTS.md](https://agents.md/)** for agent behavior instructions
- **[Agent Skills](https://agentskills.io/)** for reusable skill packages via `SKILL.md`
- **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)** for MCP server configurations
- **[GitHub Copilot CLI plugins](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating)** for native install via `copilot plugin install`

The repo is simultaneously a Copilot CLI plugin marketplace (via `.github/plugin/marketplace.json`) and a searchable web marketplace (GitHub Pages).

## Human-Centric Structure

All AI assets live under `catalog/`. Developer tooling lives under `system/`. The root stays clean.

```
catalog/skills/<name>/SKILL.md          ← standalone, reusable skills
catalog/agents/<name>.agent.md          ← standalone agent profiles
catalog/prompts/<name>.md               ← standalone slash commands
catalog/integrations/<name>/.mcp.json   ← standalone MCP server configs
catalog/plugins/<name>/plugin.json      ← wrapper or bundle (references primitives by name list)
catalog/plugins/<name>/.copilot-plugin/ ← generated Copilot-compatible package
catalog/templates/<name>/TEMPLATE.md    ← raw-download-only document templates
```

A **bundle** `plugin.json` references primitives by name list:

```json
{
  "name": "value-stream-1-default",
  "skills": ["publish-to-confluence", "generate-architecture-doc", "jira-ticket-from-code"],
  "mcpServers": ["atlassian"]
}
```

## Available Catalog Items

| Type | Name | Description | Path |
|---|---|---|---|
| Bundle | value-stream-1-default | Atlassian workflow: Confluence, architecture docs, Jira, MCP | `catalog/plugins/value-stream-1-default/` |
| MCP | atlassian-mcp | Atlassian Rovo MCP via OAuth 2.1 | `catalog/plugins/atlassian-mcp/` |
| Skill | jira-ticket-from-code | Create Jira tickets from TODO/FIXME/BUG comments | `catalog/plugins/jira-ticket-from-code/` |
| Agent | default-agent | Company-wide default agent profile | `catalog/plugins/default-agent/` |
| Prompt | pr-description-prompt | Standard PR description command | `catalog/plugins/pr-description-prompt/` |
| Template | solution-architecture | Reusable Solution Architecture document | `catalog/templates/solution-architecture/` |

Standalone skills (available via web catalog for copy/download):

| Type | Name | Description | Path |
|---|---|---|---|
| Skill | publish-to-confluence | Publish a spec or doc to a Confluence page | `catalog/skills/publish-to-confluence/` |
| Skill | generate-architecture-doc | Generate a solution architecture document | `catalog/skills/generate-architecture-doc/` |

## Quick Start

### GitHub Copilot CLI (recommended)

```bash
copilot plugin marketplace add danforceDJ/ai-catalog

# Install the full Atlassian workflow bundle
copilot plugin install value-stream-1-default@ai-catalog

# Install individual items
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
./system/scripts/install.sh mcp atlassian-mcp --ide vscode --project /path/to/project
./system/scripts/install.sh skill jira-ticket-from-code --project /path/to/project
./system/scripts/install.sh agent default-agent --project /path/to/project
./system/scripts/install.sh prompt pr-description-prompt --project /path/to/project
./system/scripts/install.sh template solution-architecture --project /path/to/project
```

Prints a deprecation banner on every invocation — prefer the Copilot CLI flow above.

## IDE Notes

- **VSCode**: MCP configuration is merged into `.vscode/mcp.json`.
- **JetBrains IntelliJ**: MCP setup is manual in AI Assistant MCP settings; `install.sh` prints exact steps.

## Repository Structure

```text
.
├── catalog/                           # All AI assets
│   ├── skills/<name>/SKILL.md         # standalone reusable skills
│   ├── agents/<name>.agent.md         # standalone agent profiles
│   ├── prompts/<name>.md              # standalone slash commands
│   ├── integrations/<name>/.mcp.json  # standalone MCP server configs
│   ├── plugins/                       # wrappers and bundles (each has plugin.json)
│   │   └── <name>/plugin.json         # references primitives by name list
│   └── templates/<name>/TEMPLATE.md   # raw-download-only templates
├── system/                            # Developer tooling (hidden from contributors)
│   ├── scripts/                       # uv-run Python generators + bash fallback
│   ├── tests/                         # test suite
│   ├── config/marketplace.config.json # marketplace metadata
│   └── artifacts/catalog.json         # generated search index
├── .github/plugin/marketplace.json    # generated — Copilot CLI entry point
├── docs/                              # generated static site (GitHub Pages)
│   ├── index.html
│   ├── catalog.json
│   └── dl/<name>.zip
├── README.md
├── START_HERE.md
└── CONTRIBUTING.md
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) to add new skills, primitives, or bundle plugins.

## Marketplace

The static marketplace page at **[danforceDJ.github.io/ai-catalog](https://danforceDJ.github.io/ai-catalog/)** is auto-generated from `system/artifacts/catalog.json` and published to GitHub Pages on every push to `main`.
