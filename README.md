# AI Catalog

A company-wide, agent-agnostic AI configuration marketplace built on three open standards:

- **[AGENTS.md](https://agents.md/)** for agent behavior instructions
- **[Agent Skills](https://agentskills.io/)** for reusable skill packages via `SKILL.md`
- **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)** for MCP server configurations

This repository is Git-platform agnostic and is designed to work on GitHub and GitLab without changing core files.

## Available Catalog Items

| Type | Name | Description | Path |
|---|---|---|---|
| MCP Server | atlassian | Atlassian Rovo MCP server via OAuth 2.1 SSO | `mcp/atlassian/` |
| Skill | jira-ticket-from-code | Create Jira tickets from TODO/FIXME/BUG code comments | `skills/jira-ticket-from-code/` |
| Agent Profile | default | Company-wide default agent profile | `agents/default/` |

## Quick Start

### VSCode

```bash
./scripts/install.sh mcp atlassian --ide vscode --project /path/to/project
./scripts/install.sh skill jira-ticket-from-code --project /path/to/project
```

### JetBrains IntelliJ

```bash
./scripts/install.sh mcp atlassian --ide jetbrains --project /path/to/project
./scripts/install.sh skill jira-ticket-from-code --project /path/to/project
```

## IDE Notes

- **VSCode**: MCP configuration is merged into `.vscode/mcp.json`.
- **JetBrains IntelliJ**: MCP setup is manual in AI Assistant MCP settings; `install.sh` prints exact steps.

## Repository Structure

```text
.
├── AGENTS.md
├── CONTRIBUTING.md
├── agents/
│   └── default/AGENTS.md
├── mcp/
│   └── atlassian/
│       ├── README.md
│       └── vscode.mcp.json
├── skills/
│   └── jira-ticket-from-code/SKILL.md
└── scripts/
    ├── generate-catalog.sh
    └── install.sh
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) to add new MCP servers, skills, and agent profiles.
