# Current Catalog Contents

> **For LLMs:** This file describes what is currently registered in the catalog.
> To add new items, see [`catalog-items.md`](catalog-items.md) for schemas and [`architecture.md`](architecture.md) for where files go.

---

## Plugins (5) — Copilot CLI Installable

All 5 use **list-reference style** in `plugin.json`. Install: `copilot plugin install <name>@ai-catalog`

| Name | Type | Version | Components |
|---|---|---|---|
| `atlassian-mcp` | mcp | 1.0.0 | mcpServers: `[atlassian]` |
| `default-agent` | agent | 1.0.0 | agents: `[default]` |
| `jira-ticket-from-code` | skill | 1.0.0 | skills: `[jira-ticket-from-code]` |
| `pr-description-prompt` | prompt | 1.0.0 | commands: `[pr-description]` |
| `value-stream-1-default` | bundle | 1.0.0 | skills: `[publish-to-confluence, generate-architecture-doc, jira-ticket-from-code]`, mcpServers: `[atlassian]` |

---

## Skills (3)

| Name | Path | Description | Used by plugin |
|---|---|---|---|
| `jira-ticket-from-code` | `skills/jira-ticket-from-code/SKILL.md` | Creates Jira tickets from TODO/FIXME/BUG comments. Uses Atlassian MCP `create_issue` tool. | `jira-ticket-from-code`, `value-stream-1-default` |
| `generate-architecture-doc` | `skills/generate-architecture-doc/SKILL.md` | Generates architecture docs (Overview, Diagram, Components, Data Flow, NFRs, Trade-offs) | `value-stream-1-default` |
| `publish-to-confluence` | `skills/publish-to-confluence/SKILL.md` | Publishes docs/specs to Confluence via Atlassian MCP `create_page`/`update_page` | `value-stream-1-default` |

---

## Agents (1)

| Name | Path | Description |
|---|---|---|
| `default` | `agents/default.agent.md` | Company-wide default agent profile. References available MCP servers and skills inline. |

Wrapped by: `plugins/default-agent/`

---

## Commands / Slash Commands (1)

| Name | Path | Description |
|---|---|---|
| `pr-description` | `commands/pr-description.md` | Standard PR description template (Summary / Changes / Test Plan / Notes sections) |

Wrapped by: `plugins/pr-description-prompt/`

---

## MCP Servers (1)

| Name | Path | Transport | Auth | Runtime |
|---|---|---|---|---|
| `atlassian` | `mcpServers/atlassian/.mcp.json` | `stdio` via `npx mcp-remote@latest` | OAuth 2.1 (no stored tokens) | Node.js 18+ |

Endpoint: `https://mcp.atlassian.com/v1/sse`

Wrapped by: `plugins/atlassian-mcp/`, `plugins/value-stream-1-default/`

---

## Templates (1)

| Name | Path | Category | Description |
|---|---|---|---|
| `solution-architecture` | `templates/solution-architecture/TEMPLATE.md` | architecture | Structured doc template: Context, Goals, High-Level Arch, Components, Data Flow, Key Decisions, Risks, Open Questions |

