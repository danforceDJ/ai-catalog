# Contributing

Thanks for contributing to the AI catalog.

## Naming Conventions

Use lowercase with hyphens for all catalog item names:

- MCP servers: `mcp/<name>/`
- Skills: `skills/<name>/`
- Agent profiles: `agents/<name>/`

Examples: `atlassian`, `jira-ticket-from-code`, `default`.

## Add a New MCP Server

1. Create `mcp/<name>/`.
2. Add `README.md` with setup instructions.
3. Add `vscode.mcp.json` when a VSCode MCP config is available.
4. Follow the MCP spec: https://modelcontextprotocol.io/

## Add a New Skill

1. Create `skills/<name>/SKILL.md`.
2. Ensure it is Agent Skills compliant with YAML frontmatter and Markdown body.
3. Include metadata such as `name`, `description`, and `version`.
4. Follow the spec: https://agentskills.io/

## Add a New Agent Profile

1. Create `agents/<name>/AGENTS.md`.
2. Define reusable behavior instructions for the profile.
3. Follow the AGENTS.md standard: https://agents.md/

## Update Catalog

After adding items, regenerate the catalog:

```bash
./scripts/generate-catalog.sh
```
