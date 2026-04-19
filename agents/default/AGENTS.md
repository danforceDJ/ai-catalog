---
name: default
description: Company-wide default agent profile enforcing git workflow, security, and conventional commit conventions.
---

# Default Agent Profile

## General Rules

- Follow the existing code style and project conventions.
- Write or update tests for behavior changes when test infrastructure exists.
- Never commit secrets or credentials.
- Keep documentation and user-facing text in English.

## Git Workflow

- Use conventional commits.
- Keep one logical change per commit.
- Never commit directly to `main`.

## Security

- Do not read `.env`, secret, or `.pem` files unless explicitly required and authorized.
- Do not hardcode internal-only URLs or credentials.
- Flag potential security issues in code and dependencies.

## Available MCP Servers

- `atlassian` (`mcp/atlassian`)

## Available Skills

- `jira-ticket-from-code` (`skills/jira-ticket-from-code`)
