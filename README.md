# AI Catalog

**🌐 [danforceDJ.github.io/ai-catalog](https://danforceDJ.github.io/ai-catalog/)** — live searchable marketplace

A company-wide AI configuration marketplace. Install skills, agent profiles, MCP servers, and prompts directly into your AI tools.

> **Not a developer?** Use the web marketplace above — browse, copy, or download any item in one click.

## Catalog

| Type | Name | Description |
|---|---|---|
| Bundle | `value-stream-1-default` | Atlassian workflow: Confluence, architecture docs, Jira tickets, MCP |
| MCP | `atlassian-mcp` | Atlassian Rovo MCP via OAuth 2.1 |
| Skill | `jira-ticket-from-code` | Create Jira tickets from TODO/FIXME/BUG code comments |
| Skill | `generate-architecture-doc` | Generate structured solution architecture documents |
| Skill | `publish-to-confluence` | Publish docs/specs to Confluence via MCP |
| Agent | `default-agent` | Company-wide default agent profile |
| Prompt | `pr-description-prompt` | Standard PR description slash command |
| Template | `solution-architecture` | Solution Architecture document template |

## Install via GitHub Copilot CLI

```bash
# Add the marketplace once
copilot plugin marketplace add danforceDJ/ai-catalog

# Install items
copilot plugin install value-stream-1-default@ai-catalog
copilot plugin install atlassian-mcp@ai-catalog
copilot plugin install jira-ticket-from-code@ai-catalog
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) to add skills, agents, prompts, MCP configs, or bundle plugins.
