# Atlassian MCP (SSO)

The Atlassian Rovo MCP Server uses OAuth 2.1 (SSO). No API tokens are required in this repository.

## Prerequisites

- Node.js 18+
- Company Atlassian Cloud account with SSO access

## Install (VSCode)

Option A (recommended):

```bash
./scripts/install.sh mcp atlassian --ide vscode --project /path/to/project
```

Option B (manual): copy `vscode.mcp.json` into your project's `.vscode/mcp.json` (or merge the `servers.atlassian` entry).

## Install (JetBrains IntelliJ)

In IntelliJ go to:

`Settings → Tools → AI Assistant → MCP`

Add a stdio server:

- Command: `npx`
- Args: `-y mcp-remote@latest https://mcp.atlassian.com/v1/sse`

You can also run:

```bash
./scripts/install.sh mcp atlassian --ide jetbrains
```

for a reminder of these steps.

## Verification

Ask your agent:

> List my open Jira tickets
