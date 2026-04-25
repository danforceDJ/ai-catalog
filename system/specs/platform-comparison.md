# Cross-Platform Plugin Marketplace Technical Specification

> **Audience:** Software architects and developers maintaining `ai-catalog` and integrating with  
> GitHub Copilot CLI, Claude Code (Claude CLI), and VS Code agent plugins.  
> **Status:** Authoritative reference — updated April 2026.  
> **Sources:** GitHub Copilot CLI docs, Claude Code docs, VS Code Copilot customization docs, and
> reverse-engineered schema from live scripts in this repository (`validate_catalog.py`,
> `generate_catalog.py`, `generate_marketplace.py`).

---

## Table of Contents

1. [Platform Overview Comparison](#1-platform-overview-comparison)
2. [GitHub Copilot CLI — Deep Dive](#2-github-copilot-cli--deep-dive)
3. [Claude Code (Claude CLI) — Deep Dive](#3-claude-code-claude-cli--deep-dive)
4. [VS Code Agent Plugins — Deep Dive](#4-vs-code-agent-plugins--deep-dive)
5. [Cross-Platform Incompatibility Table](#5-cross-platform-incompatibility-table)
6. [Multi-Platform Strategy for ai-catalog](#6-multi-platform-strategy-for-ai-catalog)
7. [Full JSON Schemas](#7-full-json-schemas)
8. [Directory Structure Reference](#8-directory-structure-reference)
9. [Migration Alignment (Rename Proposal)](#9-migration-alignment-rename-proposal)

---

## 1. Platform Overview Comparison

| Capability | GitHub Copilot CLI | Claude Code (Claude CLI) | VS Code Agent Plugins |
|---|---|---|---|
| **Manifest filename** | `plugin.json` | `claude-plugin.json` (proposed) | `package.json` (`contributes.*`) |
| **Marketplace index** | `.github/plugin/marketplace.json` | Marketplace registry URL | VS Code Extension Marketplace |
| **CLI install command** | `copilot plugin install <name>@<marketplace>` | `claude plugin install <name>` | Extension install via UI or `code --install-extension` |
| **Content types** | Skills, Agents, Commands (prompts), MCP Servers, LSP Servers, Hooks | MCP Servers, Slash Commands, Project Context | MCP Servers, Prompt templates, Instructions, Chat Participants |
| **MCP integration style** | `.mcp.json` file inside plugin dir or referenced from `mcpServers/` | `servers` block in project/user config, or `.mcp.json` | `.vscode/mcp.json` workspace file or extension `contributes.mcpServers` |
| **Auth model** | OAuth/SSO at MCP server level; no secrets in repo | OAuth/SSO at MCP server level; project `.mcp.json` scoped | OAuth/SSO; `vscode:mcp/install` deeplink triggers consent flow |
| **Discovery** | Git repo URL added as marketplace source | Marketplace registry; direct git URL | VS Code Extension Marketplace (`.vsix`); workspace-local files |
| **Naming convention** | kebab-case, ≤ 64 chars | kebab-case (inferred) | Extension publisher/name ID (e.g., `publisher.extension-name`) |
| **Scope** | Team/org via shared git repo | Project-level or user-level | Workspace, user, or org policy |
| **Deeplink support** | No deeplink; install via CLI only | No deeplink | `vscode:mcp/install?name=…&config=…` |
| **Offline/airgap** | Yes — git repo served internally | Yes — local filesystem paths | Yes — `.vsix` file install |

---

## 2. GitHub Copilot CLI — Deep Dive

### 2.1 How It Works

GitHub Copilot CLI allows teams to share AI configuration via git repositories. A _marketplace_ is
any git repository containing `.github/plugin/marketplace.json`. Users add a marketplace once:

```bash
copilot plugin marketplace add danforceDJ/ai-catalog
# or with a full URL for GitLab / self-hosted:
copilot plugin marketplace add https://gitlab.example.com/team/ai-catalog
```

Then install individual plugins by name:

```bash
copilot plugin install atlassian-mcp@ai-catalog
copilot plugin install jira-ticket-from-code@ai-catalog
copilot plugin list
copilot plugin update atlassian-mcp
copilot plugin remove atlassian-mcp
```

### 2.2 `plugin.json` — Plugin Manifest

Every installable unit (a _plugin_ or _package_) has a `plugin.json` at its root. This is the
single Copilot CLI-native manifest file — its name is **fixed** by the spec.

#### 2.2.1 Field Reference

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `name` | `string` | **Yes** | kebab-case, ≤ 64 chars | Unique identifier; must equal directory name |
| `description` | `string` | No | ≤ 1024 chars | Human-readable description displayed in marketplace |
| `version` | `string` | No | Semver recommended | Plugin version |
| `author` | `object` | No | Must have `name` sub-field | Plugin author information |
| `author.name` | `string` | No | — | Author display name |
| `author.email` | `string` | No | — | Author email |
| `author.url` | `string` | No | — | Author URL |
| `homepage` | `string` | No | — | Plugin documentation URL |
| `repository` | `string` | No | — | Source repository URL |
| `license` | `string` | No | SPDX ID recommended | License identifier |
| `keywords` | `string[]` | No | — | Search keywords |
| `category` | `string` | No | — | Catalog category (e.g., `integrations`, `productivity`) |
| `tags` | `string[]` | No | — | Display tags |
| `skills` | `string \| string[]` | No | List = top-level refs; string = relative dir path | Skill references or local path |
| `agents` | `string \| string[]` | No | List = top-level refs; string = relative dir path | Agent profile references or local path |
| `commands` | `string \| string[]` | No | List = top-level refs; string = relative dir path | Prompt/command references or local path |
| `mcpServers` | `string \| string[] \| object` | No | List = top-level dir names; string = relative `.mcp.json` path; object = inline config | MCP server configuration reference |
| `lspServers` | `string \| object` | No | — | LSP server configuration (advanced) |
| `hooks` | `string \| object` | No | — | Lifecycle hook scripts (install, update, remove) |

#### 2.2.2 The Two Reference Styles

**Legacy (string path — single-plugin repo, all content local):**
```json
{
  "name": "my-plugin",
  "skills": "skills",
  "agents": "agents",
  "commands": "commands",
  "mcpServers": ".mcp.json"
}
```
Copilot CLI reads content from subdirectories of the plugin directory itself.

**List-reference (this repo's style — shared primitives, thin wrapper):**
```json
{
  "name": "atlassian-mcp",
  "mcpServers": ["atlassian"]
}
```
Copilot CLI resolves `mcpServers/atlassian/.mcp.json` from the catalog root. The script
`generate_marketplace.py` materializes these references into a `.copilot-plugin/` compatibility
directory before publishing the marketplace index.

#### 2.2.3 Inline MCP Server Config (object style)

```json
{
  "name": "github-mcp",
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

### 2.3 `.mcp.json` — MCP Server Config File

The MCP server configuration file follows the Model Context Protocol server config format. It is
referenced from `plugin.json` via the `mcpServers` field (as a path string, e.g., `".mcp.json"`).

```json
{
  "servers": {
    "<server-name>": {
      "type": "stdio | sse | http",
      "command": "<executable>",
      "args": ["<arg1>", "<arg2>"],
      "env": {
        "ENV_VAR": "<value>"
      },
      "url": "<url-for-sse-or-http-type>"
    }
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `servers` | `object` | **Yes** | Map of server name → server config |
| `servers.<name>.type` | `enum` | **Yes** | Transport: `stdio`, `sse`, or `http` |
| `servers.<name>.command` | `string` | For `stdio` | Executable path or command name |
| `servers.<name>.args` | `string[]` | No | Arguments to the executable |
| `servers.<name>.env` | `object` | No | Environment variables (values must NOT be secrets) |
| `servers.<name>.url` | `string` | For `sse`/`http` | SSE or HTTP endpoint URL |

**Security rule (enforced by `validate_catalog.py`):** If any value in `env` or any field matches
patterns like `password=`, `api_key=`, `ghp_…`, `API_TOKEN="…"`, CI validation fails.

### 2.4 `.github/plugin/marketplace.json` — Marketplace Index

This file is the catalog consumed by `copilot plugin marketplace add`. It is generated by
`generate_marketplace.py` from `marketplace.config.json` + `plugins/*/plugin.json`.

#### 2.4.1 Field Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | **Yes** | Marketplace identifier (kebab-case, ≤ 64 chars) |
| `owner` | `object` | **Yes** | Marketplace owner |
| `owner.name` | `string` | **Yes** | Owner username or org name |
| `owner.email` | `string` | No | Owner email |
| `metadata` | `object` | No | Freeform marketplace metadata (description, version, etc.) |
| `plugins` | `array` | **Yes** | Ordered list of plugin entries |
| `plugins[].name` | `string` | **Yes** | Plugin name (kebab-case, ≤ 64 chars) |
| `plugins[].source` | `string \| object` | **Yes** | Path to the plugin directory (relative to repo root) or config object |
| `plugins[].description` | `string` | No | Plugin description (passthrough from `plugin.json`) |
| `plugins[].version` | `string` | No | Plugin version (passthrough) |
| `plugins[].author` | `object` | No | Author (passthrough) |
| `plugins[].license` | `string` | No | License (passthrough) |
| `plugins[].keywords` | `string[]` | No | Keywords (passthrough) |
| `plugins[].category` | `string` | No | Category (passthrough) |
| `plugins[].tags` | `string[]` | No | Tags (passthrough) |
| `plugins[].skills` | `string` | No | Materialized skill path (passthrough from compat dir) |
| `plugins[].agents` | `string` | No | Materialized agent path (passthrough) |
| `plugins[].commands` | `string` | No | Materialized commands path (passthrough) |
| `plugins[].mcpServers` | `object` | No | Resolved MCP server config objects (not raw names) |
| `plugins[].hooks` | `string \| object` | No | Hooks config (passthrough) |
| `plugins[].lspServers` | `string \| object` | No | LSP server config (passthrough) |

#### 2.4.2 The `source` Field

The `source` value is a **relative path to a directory** containing a `plugin.json`. For
list-reference plugins, this points to the generated `.copilot-plugin/` directory, not the raw
`plugins/<name>/` directory:

```json
{
  "name": "atlassian-mcp",
  "source": "plugins/atlassian-mcp/.copilot-plugin"
}
```

The `.copilot-plugin/` directory contains a flattened `plugin.json` with string paths (not lists)
and all referenced files copied in.

### 2.5 Materialization Flow

```
plugins/atlassian-mcp/plugin.json   (list-reference style)
    "mcpServers": ["atlassian"]
         ↓  generate_marketplace.py
reads:  mcpServers/atlassian/.mcp.json
writes: plugins/atlassian-mcp/.copilot-plugin/
            plugin.json             (flattened: "mcpServers": ".mcp.json")
            .mcp.json               (merged server configs)
         ↓
.github/plugin/marketplace.json
    "source": "plugins/atlassian-mcp/.copilot-plugin"
```

### 2.6 `catalog.json` — Search Index (this repo's extension)

`catalog.json` is not a Copilot CLI standard — it is this repository's search index format,
generated by `generate_catalog.py` for the static web marketplace UI.

```json
{
  "plugins": [
    {
      "name": "atlassian-mcp",
      "description": "...",
      "version": "1.0.0",
      "type": "mcp",
      "category": "integrations",
      "tags": ["atlassian", "mcp"],
      "keywords": ["atlassian", "jira"],
      "components": {
        "skills": [],
        "agents": [],
        "commands": [],
        "mcpServers": ["atlassian"],
        "hooks": false
      },
      "install": {
        "copilot": "atlassian-mcp@ai-catalog",
        "vscodeMcpDeeplink": "vscode:mcp/install?name=atlassian&config=<base64>",
        "rawFiles": [],
        "zip": "dl/atlassian-mcp.zip",
        "repoPath": "plugins/atlassian-mcp"
      }
    }
  ],
  "templates": [...]
}
```

**`type` derivation logic:**

| Components present | `type` value |
|---|---|
| Only MCP servers | `mcp` |
| Only skills | `skill` |
| Only agents | `agent` |
| Only commands | `prompt` |
| Two or more kinds | `bundle` |
| None | `empty` |

---

## 3. Claude Code (Claude CLI) — Deep Dive

### 3.1 How It Works

Claude Code (also called Claude CLI, accessed via `claude` command) supports a plugin marketplace
system that allows teams to distribute AI configuration — primarily MCP server configs,
slash command definitions, and project context instructions — through git repositories.

Users add a marketplace and install plugins similarly to Copilot CLI:

```bash
claude plugin marketplace add https://github.com/danforceDJ/ai-catalog
claude plugin install atlassian-mcp
claude plugin list
claude plugin remove atlassian-mcp
```

### 3.2 MCP Configuration in Claude Code

Claude Code resolves MCP server configurations from multiple layers, in precedence order:

| Source | Path | Scope | Description |
|---|---|---|---|
| User global config | `~/.claude/claude_desktop_config.json` | User | Always-on MCP servers for the user |
| Project config | `.claude/claude_desktop_config.json` (project root) | Project | Project-specific MCP servers |
| Installed plugin | Via `claude plugin install` (written to user config) | User | Installed from marketplace |
| Environment variable | `ANTHROPIC_API_KEY`, etc. | Process | Runtime auth |

The MCP config format used by Claude Code follows the **Claude Desktop** config schema:

```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "<executable>",
      "args": ["<arg1>"],
      "env": {
        "KEY": "value"
      }
    }
  }
}
```

> **Key difference from Copilot CLI:** Claude Desktop/Claude Code uses `mcpServers` as the top-level
> key (not `servers`). Copilot CLI uses `servers`. Both reference the same MCP protocol.

### 3.3 Plugin Marketplace Manifest (Claude Code)

The Claude Code marketplace spec is actively evolving. Based on available documentation,
a Claude marketplace index is a JSON file hosted at a known URL or git path:

```json
{
  "name": "ai-catalog",
  "version": "1.0.0",
  "description": "Team AI configuration marketplace",
  "plugins": [
    {
      "name": "atlassian-mcp",
      "description": "Atlassian Rovo MCP Server via OAuth",
      "version": "1.0.0",
      "source": {
        "type": "git",
        "url": "https://github.com/danforceDJ/ai-catalog",
        "path": "plugins/atlassian-mcp"
      },
      "manifest": "claude-plugin.json",
      "category": "integrations",
      "tags": ["atlassian", "jira", "mcp"]
    }
  ]
}
```

### 3.4 Per-Plugin Manifest (`claude-plugin.json`)

The per-plugin manifest for Claude Code (proposed/emerging format):

```json
{
  "name": "atlassian-mcp",
  "description": "Atlassian Rovo MCP Server via OAuth 2.1",
  "version": "1.0.0",
  "author": "danforceDJ",
  "license": "MIT",
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://mcp.atlassian.com/v1/sse"]
    }
  },
  "slashCommands": [
    {
      "name": "pr-description",
      "description": "Generate a PR description",
      "prompt": "commands/pr-description.md"
    }
  ],
  "instructions": "agents/default.agent.md"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | **Yes** | Plugin identifier |
| `description` | `string` | No | Human-readable description |
| `version` | `string` | No | Semver version |
| `author` | `string \| object` | No | Plugin author |
| `license` | `string` | No | SPDX license identifier |
| `mcpServers` | `object` | No | Claude Desktop-format MCP server configs (key = server name) |
| `slashCommands` | `array` | No | Slash command definitions |
| `slashCommands[].name` | `string` | Yes | Command name (becomes `/name` in Claude) |
| `slashCommands[].description` | `string` | No | Command description |
| `slashCommands[].prompt` | `string` | No | Path to prompt Markdown file |
| `instructions` | `string \| string[]` | No | Path(s) to `.md` instruction files (project context) |

### 3.5 Slash Commands in Claude Code

Claude Code supports project-level slash commands defined in `.claude/commands/` or installed via
plugins. Each command is a Markdown file with YAML frontmatter:

```markdown
---
name: pr-description
description: Generate a structured pull request description
---

Generate a PR description with these sections:

## Summary
<!-- What does this PR do? -->

## Changes
<!-- Bullet list of key changes -->
```

When installed, the command is available as `/pr-description` in Claude Code sessions within the
project scope.

### 3.6 Project Context (CLAUDE.md / `.claude/`)

Claude Code reads `CLAUDE.md` at the project root as persistent project context. Plugin
installation can add to `.claude/` directory:

```
.claude/
├── CLAUDE.md           → always-on project instructions
├── commands/
│   └── *.md            → installed slash commands
└── claude_desktop_config.json  → project MCP server config
```

---

## 4. VS Code Agent Plugins — Deep Dive

### 4.1 How It Works

VS Code supports AI customization through three overlapping mechanisms:

1. **VS Code Extensions** — traditional `.vsix` packages that can contribute chat participants,
   MCP server configs, and prompt templates via the `contributes` manifest key.
2. **Workspace-local files** — `.github/prompts/`, `.github/instructions/`, `.vscode/mcp.json`
   in any repository automatically activate in Copilot Chat.
3. **`vscode:mcp/install` deeplink** — a one-click URL that installs a specific MCP server
   configuration into VS Code user settings.

### 4.2 Workspace-Local AI Customization Files

These files are auto-discovered by VS Code Copilot Chat when present in the repository:

#### 4.2.1 `.github/prompts/*.prompt.md` — Reusable Prompt Templates

```markdown
---
mode: ask | edit | agent
tools:
  - fetch
  - github
  - codebase
description: Generate a structured pull request description
---

Generate a PR description for the current branch changes.

## Summary
<!-- What does this PR do? -->
```

| Frontmatter Field | Type | Required | Description |
|---|---|---|---|
| `mode` | `enum` | No | Chat mode: `ask` (default), `edit`, or `agent` |
| `tools` | `string[]` | No | Tool names available in this prompt context |
| `description` | `string` | No | Shown in the prompt picker UI |

Files appear as slash commands in Copilot Chat: `/pr-description` (filename stem is the command).

#### 4.2.2 `.github/instructions/*.instructions.md` — Always-On Instructions

```markdown
---
applyTo: "**/*.ts,**/*.tsx"
---

# TypeScript Coding Standards

- Always use `const` over `let` unless reassignment is needed.
- Prefer explicit return types on exported functions.
```

| Frontmatter Field | Type | Required | Description |
|---|---|---|---|
| `applyTo` | `string` | No | Glob pattern for files where these instructions apply; `**` = always |

These files inject persistent context into every Copilot Chat session, scoped to matching files.

#### 4.2.3 `.vscode/mcp.json` — Workspace MCP Server Config

```json
{
  "servers": {
    "atlassian": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://mcp.atlassian.com/v1/sse"]
    },
    "github": {
      "type": "sse",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer ${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

> **Note:** VS Code uses `servers` (same as Copilot CLI `.mcp.json`), while Claude Desktop uses
> `mcpServers` as the top-level key.

MCP server types supported by VS Code:

| `type` value | Transport | Required fields |
|---|---|---|
| `stdio` | Process stdio | `command`, optionally `args`, `env` |
| `sse` | Server-Sent Events | `url`, optionally `headers` |
| `http` | HTTP streaming | `url`, optionally `headers` |

### 4.3 `vscode:mcp/install` Deeplink

The deeplink allows installing an MCP server into VS Code user settings with a single click
(e.g., from a web catalog or README badge):

```
vscode:mcp/install?name=<server-name>&config=<base64url-encoded-json>
```

**Parameters:**

| Parameter | Required | Description |
|---|---|---|
| `name` | **Yes** | MCP server name (becomes the key in settings) |
| `config` | **Yes** | Base64url-encoded (no padding) JSON of the server config object |

**Construction:**

```python
import base64, json

server_config = {
    "name": "atlassian",
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "mcp-remote@latest", "https://mcp.atlassian.com/v1/sse"]
}
payload = json.dumps(server_config, separators=(",", ":"))
encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
deeplink = f"vscode:mcp/install?name=atlassian&config={encoded}"
```

**Constraints:**
- The entire deeplink URL must stay under **2048 bytes** (enforced by `generate_catalog.py`)
- Only single-server configs are linkable; multi-server plugins fall back to zip download
- The config JSON must include the `name` field alongside transport fields

### 4.4 VS Code Extension Contributions (`package.json`)

A VS Code extension can contribute AI capabilities via these `contributes` keys:

```json
{
  "contributes": {
    "mcpServers": [
      {
        "id": "atlassian",
        "label": "Atlassian Rovo",
        "command": "npx",
        "args": ["-y", "mcp-remote@latest", "https://mcp.atlassian.com/v1/sse"]
      }
    ],
    "chatParticipants": [
      {
        "id": "my-extension.assistant",
        "name": "myassistant",
        "fullName": "My Team Assistant",
        "description": "Team-specific AI assistant",
        "isSticky": true,
        "commands": [
          {
            "name": "review",
            "description": "Review code for team standards"
          }
        ]
      }
    ],
    "languageModels": [...],
    "aiTextContent": [...]
  }
}
```

### 4.5 VS Code Settings Relevant to Agent Mode

| Setting key | Type | Description |
|---|---|---|
| `chat.mcp.enabled` | `boolean` | Enable MCP server support in Copilot Chat |
| `github.copilot.chat.agent.thinkingTool.enabled` | `boolean` | Enable extended thinking in agent mode |
| `chat.promptFiles.enabled` | `boolean` | Enable `.github/prompts/` file discovery |
| `chat.instructionsFiles.enabled` | `boolean` | Enable `.github/instructions/` file discovery |
| `github.copilot.chat.scopeSelection` | `enum` | Default scope for Copilot Chat |

---

## 5. Cross-Platform Incompatibility Table

| Area | GitHub Copilot CLI | Claude Code | VS Code | Notes |
|---|---|---|---|---|
| **MCP config top-level key** | `servers` | `mcpServers` | `servers` | Claude Desktop uses `mcpServers`; Copilot CLI and VS Code use `servers` — these are different JSON shapes |
| **MCP config file name** | `.mcp.json` (inside plugin) | `claude_desktop_config.json` or `.mcp.json` | `.vscode/mcp.json` | Three different file names; none is cross-platform |
| **Plugin manifest file** | `plugin.json` (mandatory) | `claude-plugin.json` (emerging) | `package.json` (extension) | Cannot share one file across all three |
| **Slash commands location** | `commands/` dir under plugin or top-level | `.claude/commands/` dir | `.github/prompts/` dir | Three different directory conventions |
| **Agent instructions** | `agents/` dir under plugin or top-level | `CLAUDE.md` / `.claude/` dir | `.github/instructions/` dir | Three different conventions |
| **Skills** | `skills/` dir (Copilot CLI concept) | No direct equivalent | No direct equivalent | Only Copilot CLI has "skills" as a first-class concept |
| **Marketplace discovery** | Git repo URL → `marketplace add` | Registry URL or plugin URL | Extension Marketplace (`.vsix`) | Incompatible discovery mechanisms |
| **Install command** | `copilot plugin install <name>@<mkt>` | `claude plugin install <name>` | `code --install-extension` or UI | Different CLI tools |
| **Deeplink** | Not supported | Not supported | `vscode:mcp/install?...` | VS Code-specific |
| **Naming of command list in `plugin.json`** | `"commands": [...]` | `"slashCommands": [...]` | `contributes.chatParticipants[].commands` | Different field names for same concept |
| **`mcpServers` field in plugin manifest** | List of dir names OR `.mcp.json` path OR inline object | Inline config object | Via `contributes.mcpServers` in `package.json` | All structurally different |
| **Auth/secret handling** | No secrets in repo; OAuth at MCP server | Same; `env` vars discouraged | Same; `${env:VAR}` syntax in `.vscode/mcp.json` | VS Code supports `${env:VAR}` substitution |
| **Offline/air-gap** | Full — git clone | Full — local paths | Partial — `.vsix` offline; marketplace needs internet |  |

---

## 6. Multi-Platform Strategy for ai-catalog

### 6.1 Current State

The repository currently emits artifacts for **one platform only**: GitHub Copilot CLI.

| Artifact | Platform | Status |
|---|---|---|
| `.github/plugin/marketplace.json` | Copilot CLI | ✅ Generated |
| `plugins/*/plugin.json` | Copilot CLI | ✅ Source |
| `plugins/*/.copilot-plugin/` | Copilot CLI | ✅ Generated |
| `catalog.json` | Web UI (custom) | ✅ Generated |
| `docs/index.html` | Web browser | ✅ Generated |

### 6.2 Proposed Multi-Platform Additions

To simultaneously support all three platforms, the following artifacts need to be generated:

#### For Claude Code

**New file: `claude.marketplace.json`** (or hosted as a URL)

```json
{
  "name": "ai-catalog",
  "version": "1.0.0",
  "description": "Company-wide AI configuration marketplace",
  "plugins": [
    {
      "name": "atlassian-mcp",
      "description": "Atlassian Rovo MCP Server via OAuth 2.1",
      "version": "1.0.0",
      "source": {
        "type": "git",
        "url": "https://github.com/danforceDJ/ai-catalog",
        "path": "plugins/atlassian-mcp"
      },
      "manifest": "claude-plugin.json",
      "category": "integrations",
      "tags": ["atlassian", "jira", "mcp"]
    }
  ]
}
```

**New file per plugin: `plugins/<name>/claude-plugin.json`**

Maps from `plugin.json` but transforms MCP config from `servers` key → `mcpServers` key:

```json
{
  "name": "atlassian-mcp",
  "description": "...",
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://mcp.atlassian.com/v1/sse"]
    }
  }
}
```

**New script: `scripts/generate_claude_marketplace.py`**

Reads `plugins/*/plugin.json` + `mcpServers/*/.mcp.json`, transforms `servers` → `mcpServers`,
and writes `claude.marketplace.json` + `plugins/*/claude-plugin.json`.

#### For VS Code

**New workspace MCP config: `.vscode/mcp.json`** (generated from top-level MCP server catalog)

Contains all MCP servers registered in `mcpServers/` (or `tool-connections/` post-rename), merged:

```json
{
  "servers": {
    "atlassian": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://mcp.atlassian.com/v1/sse"]
    }
  }
}
```

**New prompt files: `.github/prompts/<name>.prompt.md`** (generated from `commands/`)

Each `commands/<name>.md` file gets mirrored to `.github/prompts/<name>.prompt.md` with
frontmatter enriched with VS Code-specific fields:

```markdown
---
mode: ask
description: Generate a structured pull request description
---

<!-- original command content -->
```

**New instructions file: `.github/instructions/catalog-agent.instructions.md`** (from `agents/`)

```markdown
---
applyTo: "**"
---

<!-- content from agents/default.agent.md -->
```

### 6.3 Updated `catalog.json` — Multi-Platform Install Paths

The current `install` object in each catalog entry should be extended:

```json
{
  "install": {
    "copilot": "atlassian-mcp@ai-catalog",
    "claude": "claude plugin install atlassian-mcp",
    "vscodeMcpDeeplink": "vscode:mcp/install?name=atlassian&config=<base64>",
    "vscodeWorkspace": ".vscode/mcp.json",
    "rawFiles": [],
    "zip": "dl/atlassian-mcp.zip",
    "repoPath": "plugins/atlassian-mcp",
    "platforms": ["copilot-cli", "claude", "vscode"]
  }
}
```

### 6.4 Generation Script Changes Summary

| Script | Change needed | Priority |
|---|---|---|
| `generate_catalog.py` | Add `install.claude`, `install.platforms` fields | Medium |
| `generate_catalog.py` | Add `install.vscodeWorkspace` for MCP-type entries | Medium |
| `generate_marketplace.py` | No change to Copilot output | — |
| `scripts/generate_claude_marketplace.py` | **New script** — generates `claude.marketplace.json` | High |
| `scripts/generate_vscode_artifacts.py` | **New script** — mirrors commands → `.github/prompts/`, agents → `.github/instructions/`, MCP → `.vscode/mcp.json` | High |

### 6.5 MCP Config Format Transformation Table

This is the critical schema transformation needed between platforms:

**Source (this repo's `.mcp.json`):**
```json
{ "servers": { "atlassian": { "type": "stdio", "command": "npx", "args": [...] } } }
```

**→ VS Code `.vscode/mcp.json` (identical format):**
```json
{ "servers": { "atlassian": { "type": "stdio", "command": "npx", "args": [...] } } }
```

**→ Claude Desktop / Claude Code config:**
```json
{ "mcpServers": { "atlassian": { "command": "npx", "args": [...] } } }
```
Note: Claude omits `type` field; uses `command`+`args` directly.

**→ VS Code `vscode:mcp/install` deeplink payload:**
```json
{ "name": "atlassian", "type": "stdio", "command": "npx", "args": [...] }
```
Note: `name` field added; entire object base64url-encoded.

---

## 7. Full JSON Schemas

### 7.1 Copilot CLI `plugin.json` Schema (Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/danforceDJ/ai-catalog/specs/schemas/copilot-plugin.schema.json",
  "title": "Copilot CLI plugin.json",
  "description": "Plugin manifest for GitHub Copilot CLI installable packages.",
  "type": "object",
  "required": ["name"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Unique plugin identifier. Must match the directory name.",
      "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
      "maxLength": 64
    },
    "description": {
      "type": "string",
      "description": "Human-readable description shown in the marketplace.",
      "maxLength": 1024
    },
    "version": {
      "type": "string",
      "description": "Plugin version. Semver recommended (e.g., '1.0.0')."
    },
    "author": {
      "type": "object",
      "description": "Plugin author information.",
      "required": ["name"],
      "properties": {
        "name": { "type": "string" },
        "email": { "type": "string", "format": "email" },
        "url": { "type": "string", "format": "uri" }
      },
      "additionalProperties": false
    },
    "homepage": {
      "type": "string",
      "format": "uri",
      "description": "Plugin documentation URL."
    },
    "repository": {
      "type": "string",
      "description": "Source repository URL (URI or shorthand)."
    },
    "license": {
      "type": "string",
      "description": "SPDX license identifier (e.g., 'MIT', 'Apache-2.0')."
    },
    "keywords": {
      "type": "array",
      "description": "Search keywords.",
      "items": { "type": "string" }
    },
    "category": {
      "type": "string",
      "description": "Catalog category (e.g., 'integrations', 'productivity', 'agents')."
    },
    "tags": {
      "type": "array",
      "description": "Display tags.",
      "items": { "type": "string" }
    },
    "skills": {
      "description": "Skills: list of top-level skill names OR a relative directory path.",
      "oneOf": [
        {
          "type": "array",
          "items": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
          "description": "List-reference style: names of skill directories under top-level skills/"
        },
        {
          "type": "string",
          "description": "Legacy string style: path to skills directory relative to plugin dir."
        }
      ]
    },
    "agents": {
      "description": "Agent profiles: list of top-level agent names OR a relative directory path.",
      "oneOf": [
        {
          "type": "array",
          "items": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
          "description": "List-reference style: names of *.agent.md files under top-level agents/"
        },
        {
          "type": "string",
          "description": "Legacy string style: path to agents directory relative to plugin dir."
        }
      ]
    },
    "commands": {
      "description": "Slash commands/prompts: list of top-level command names OR a relative directory path.",
      "oneOf": [
        {
          "type": "array",
          "items": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
          "description": "List-reference style: names of *.md files under top-level commands/"
        },
        {
          "type": "string",
          "description": "Legacy string style: path to commands directory relative to plugin dir."
        }
      ]
    },
    "mcpServers": {
      "description": "MCP servers: list of top-level server names, a path to .mcp.json, or inline server configs.",
      "oneOf": [
        {
          "type": "array",
          "items": { "type": "string" },
          "description": "List-reference style: names of directories under top-level mcpServers/"
        },
        {
          "type": "string",
          "description": "Legacy string style: path to .mcp.json relative to plugin dir (e.g., '.mcp.json')"
        },
        {
          "type": "object",
          "description": "Inline MCP server config object (server name → MCP server config).",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "type": { "type": "string", "enum": ["stdio", "sse", "http"] },
              "command": { "type": "string" },
              "args": { "type": "array", "items": { "type": "string" } },
              "env": { "type": "object", "additionalProperties": { "type": "string" } },
              "url": { "type": "string" }
            }
          }
        }
      ]
    },
    "lspServers": {
      "description": "LSP server configurations (advanced use).",
      "oneOf": [
        { "type": "string" },
        { "type": "object" }
      ]
    },
    "hooks": {
      "description": "Lifecycle hooks (install, update, remove scripts).",
      "oneOf": [
        { "type": "string" },
        {
          "type": "object",
          "properties": {
            "install": { "type": "string" },
            "update": { "type": "string" },
            "remove": { "type": "string" }
          }
        }
      ]
    }
  },
  "additionalProperties": true
}
```

### 7.2 Copilot CLI `marketplace.json` Schema (Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/danforceDJ/ai-catalog/specs/schemas/copilot-marketplace.schema.json",
  "title": "Copilot CLI marketplace.json",
  "description": "Marketplace index for GitHub Copilot CLI plugin discovery.",
  "type": "object",
  "required": ["name", "owner", "plugins"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Marketplace identifier. kebab-case, ≤ 64 chars.",
      "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
      "maxLength": 64
    },
    "owner": {
      "type": "object",
      "description": "Marketplace owner (the git repository owner).",
      "required": ["name"],
      "properties": {
        "name": { "type": "string", "description": "Owner username or org name." },
        "email": { "type": "string", "format": "email" }
      },
      "additionalProperties": false
    },
    "metadata": {
      "type": "object",
      "description": "Freeform marketplace metadata.",
      "properties": {
        "description": { "type": "string" },
        "version": { "type": "string" },
        "homepage": { "type": "string", "format": "uri" }
      },
      "additionalProperties": true
    },
    "plugins": {
      "type": "array",
      "description": "Ordered list of plugin entries in this marketplace.",
      "items": {
        "type": "object",
        "required": ["name", "source"],
        "properties": {
          "name": {
            "type": "string",
            "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
            "maxLength": 64,
            "description": "Plugin name matching plugin.json name."
          },
          "source": {
            "description": "Path to plugin directory relative to repo root. For list-reference plugins, points to .copilot-plugin/ subdir.",
            "oneOf": [
              { "type": "string", "description": "Relative directory path." },
              { "type": "object", "description": "Config object (future extension)." }
            ]
          },
          "description": { "type": "string" },
          "version": { "type": "string" },
          "author": { "type": "object" },
          "license": { "type": "string" },
          "homepage": { "type": "string" },
          "keywords": { "type": "array", "items": { "type": "string" } },
          "category": { "type": "string" },
          "tags": { "type": "array", "items": { "type": "string" } },
          "skills": { "type": "string", "description": "Materialized skill directory path." },
          "agents": { "type": "string", "description": "Materialized agents directory path." },
          "commands": { "type": "string", "description": "Materialized commands directory path." },
          "mcpServers": {
            "description": "Resolved MCP server config objects (not raw name list).",
            "oneOf": [
              { "type": "string", "description": "Legacy path to .mcp.json" },
              { "type": "object", "description": "Inline server config map." }
            ]
          },
          "hooks": { "oneOf": [{ "type": "string" }, { "type": "object" }] },
          "lspServers": { "oneOf": [{ "type": "string" }, { "type": "object" }] }
        },
        "additionalProperties": true
      }
    }
  },
  "additionalProperties": true
}
```

### 7.3 Claude Code Plugin Manifest Schema (Emerging — Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/danforceDJ/ai-catalog/specs/schemas/claude-plugin.schema.json",
  "title": "Claude Code claude-plugin.json",
  "description": "Plugin manifest for Claude Code (claude CLI) installable packages.",
  "type": "object",
  "required": ["name"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Plugin identifier. kebab-case, ≤ 64 chars.",
      "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
      "maxLength": 64
    },
    "description": { "type": "string", "maxLength": 1024 },
    "version": { "type": "string" },
    "author": {
      "oneOf": [
        { "type": "string" },
        {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "email": { "type": "string" }
          }
        }
      ]
    },
    "license": { "type": "string" },
    "mcpServers": {
      "type": "object",
      "description": "MCP servers in Claude Desktop format (mcpServers, not servers).",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "command": { "type": "string" },
          "args": { "type": "array", "items": { "type": "string" } },
          "env": { "type": "object", "additionalProperties": { "type": "string" } }
        }
      }
    },
    "slashCommands": {
      "type": "array",
      "description": "Slash command definitions.",
      "items": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
          "description": { "type": "string" },
          "prompt": { "type": "string", "description": "Relative path to Markdown prompt file." }
        }
      }
    },
    "instructions": {
      "description": "Path(s) to instruction/context Markdown files.",
      "oneOf": [
        { "type": "string" },
        { "type": "array", "items": { "type": "string" } }
      ]
    }
  },
  "additionalProperties": true
}
```

### 7.4 Claude Code Marketplace Index Schema (Emerging — Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/danforceDJ/ai-catalog/specs/schemas/claude-marketplace.schema.json",
  "title": "Claude Code marketplace index",
  "description": "Marketplace index for Claude Code plugin discovery.",
  "type": "object",
  "required": ["name", "plugins"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Marketplace identifier.",
      "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$"
    },
    "version": { "type": "string" },
    "description": { "type": "string" },
    "plugins": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "source"],
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" },
          "version": { "type": "string" },
          "source": {
            "type": "object",
            "required": ["type", "url"],
            "properties": {
              "type": { "type": "string", "enum": ["git", "url", "local"] },
              "url": { "type": "string" },
              "path": { "type": "string", "description": "Sub-path within the git repo." },
              "ref": { "type": "string", "description": "Git branch, tag, or SHA." }
            }
          },
          "manifest": {
            "type": "string",
            "description": "Manifest filename within the plugin directory.",
            "default": "claude-plugin.json"
          },
          "category": { "type": "string" },
          "tags": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  },
  "additionalProperties": true
}
```

### 7.5 `.mcp.json` / `.vscode/mcp.json` Server Config Schema (Copilot CLI + VS Code format)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/danforceDJ/ai-catalog/specs/schemas/mcp-config.schema.json",
  "title": "MCP Server Config (.mcp.json)",
  "description": "Model Context Protocol server configuration. Used by Copilot CLI and VS Code.",
  "type": "object",
  "required": ["servers"],
  "properties": {
    "servers": {
      "type": "object",
      "description": "Map of server name → MCP server configuration.",
      "additionalProperties": {
        "type": "object",
        "required": ["type"],
        "properties": {
          "type": {
            "type": "string",
            "enum": ["stdio", "sse", "http"],
            "description": "Transport mechanism."
          },
          "command": {
            "type": "string",
            "description": "Executable command. Required for stdio type."
          },
          "args": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Command arguments."
          },
          "env": {
            "type": "object",
            "description": "Environment variables. MUST NOT contain secrets.",
            "additionalProperties": { "type": "string" }
          },
          "url": {
            "type": "string",
            "format": "uri",
            "description": "Server URL. Required for sse and http types."
          },
          "headers": {
            "type": "object",
            "description": "HTTP headers (VS Code only). Use ${env:VAR} substitution for secrets.",
            "additionalProperties": { "type": "string" }
          }
        }
      }
    }
  }
}
```

### 7.6 `catalog.json` Search Index Schema (this repo)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/danforceDJ/ai-catalog/specs/schemas/catalog.schema.json",
  "title": "ai-catalog catalog.json",
  "description": "Search index generated by generate_catalog.py. Powers the static web marketplace.",
  "type": "object",
  "required": ["plugins", "templates"],
  "properties": {
    "plugins": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "type", "install"],
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" },
          "version": { "type": "string" },
          "type": {
            "type": "string",
            "enum": ["mcp", "skill", "agent", "prompt", "bundle", "empty"],
            "description": "Derived from which component types are non-empty."
          },
          "category": { "type": "string" },
          "tags": { "type": "array", "items": { "type": "string" } },
          "keywords": { "type": "array", "items": { "type": "string" } },
          "components": {
            "type": "object",
            "properties": {
              "skills": { "type": "array", "items": { "type": "string" } },
              "agents": { "type": "array", "items": { "type": "string" } },
              "commands": { "type": "array", "items": { "type": "string" } },
              "mcpServers": { "type": "array", "items": { "type": "string" } },
              "hooks": { "type": "boolean" }
            }
          },
          "install": {
            "type": "object",
            "properties": {
              "copilot": { "type": ["string", "null"], "description": "<name>@<marketplace> install string" },
              "vscodeMcpDeeplink": { "type": ["string", "null"], "description": "vscode:mcp/install?... deeplink" },
              "rawFiles": { "type": "array", "items": { "type": "string" } },
              "zip": { "type": "string", "description": "Relative path to generated .zip" },
              "repoPath": { "type": "string", "description": "Source directory path within repo" }
            }
          }
        }
      }
    },
    "templates": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "type", "install"],
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" },
          "version": { "type": "string" },
          "type": { "type": "string", "const": "template" },
          "category": { "type": "string" },
          "tags": { "type": "array", "items": { "type": "string" } },
          "keywords": { "type": "array", "items": { "type": "string" } },
          "install": {
            "type": "object",
            "properties": {
              "rawFiles": { "type": "array", "items": { "type": "string" } },
              "zip": { "type": "string" },
              "repoPath": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

---

## 8. Directory Structure Reference

### 8.1 GitHub Copilot CLI — Required Structure

```
ai-catalog/                          ← git repository root
│
├── .github/
│   └── plugin/
│       └── marketplace.json         ← MARKETPLACE INDEX (generated; tracked in git)
│
├── marketplace.config.json          ← Marketplace owner/name config (source of truth)
│
├── plugins/                         ← One directory per installable plugin
│   └── atlassian-mcp/
│       ├── plugin.json              ← PLUGIN MANIFEST (Copilot CLI spec; mandatory filename)
│       └── .copilot-plugin/         ← GENERATED compatibility dir (gitignored or tracked?)
│           ├── plugin.json          ← Flattened manifest (string paths, not lists)
│           └── .mcp.json            ← Merged MCP server configs
│
├── skills/                          ← Top-level shared skill primitives
│   └── jira-ticket-from-code/
│       └── SKILL.md                 ← Skill definition with YAML frontmatter
│
├── agents/                          ← Top-level shared agent profiles
│   └── default.agent.md             ← Agent profile with YAML frontmatter
│
├── commands/                        ← Top-level shared prompt/command definitions
│   └── pr-description.md            ← Slash command with YAML frontmatter
│
├── mcpServers/                      ← Top-level shared MCP server configs
│   └── atlassian/
│       └── .mcp.json                ← MCP server config (servers format)
│
└── templates/                       ← Document templates (web-only, not CLI-installable)
    └── solution-architecture/
        └── TEMPLATE.md
```

**Key invariants:**
- `plugin.json` `name` field **must** equal the directory name
- `commands/*.md` frontmatter `name` **must** equal the file stem
- `.mcp.json` must not contain secrets
- `marketplace.json` `plugins[].source` must be a valid directory path

### 8.2 Claude Code — Required Structure

```
project-root/
│
├── CLAUDE.md                        ← Project-level persistent context (always read)
│
├── .claude/
│   ├── claude_desktop_config.json   ← Project MCP server config (mcpServers format)
│   └── commands/
│       └── pr-description.md        ← Slash command (available as /pr-description)
│
│   ← For a Claude marketplace plugin repo: ←
├── plugins/
│   └── atlassian-mcp/
│       └── claude-plugin.json       ← Claude plugin manifest
│
└── claude.marketplace.json          ← Claude marketplace index
```

**User-global Claude config:**
```
~/.claude/
├── claude_desktop_config.json       ← Global MCP servers always active
├── CLAUDE.md                        ← Global persistent context
└── commands/
    └── *.md                         ← Global slash commands
```

### 8.3 VS Code Agent Plugins — Required Structure

```
project-root/
│
├── .vscode/
│   └── mcp.json                     ← Workspace MCP server config (servers format)
│
├── .github/
│   ├── prompts/
│   │   └── pr-description.prompt.md ← Prompt template → /pr-description slash command
│   │
│   └── instructions/
│       └── coding-standards.instructions.md  ← Always-on instructions (applyTo glob)
│
│   ← For a VS Code Extension: ←
├── package.json
│   └── contributes:
│       ├── mcpServers: [...]         ← Extension-contributed MCP servers
│       ├── chatParticipants: [...]   ← Chat participants (@participant)
│       └── languageModels: [...]     ← (advanced) custom models
│
└── README.md
    └── [![Install MCP](badge)](vscode:mcp/install?name=atlassian&config=<b64>)
                                     ← One-click deeplink in README or web catalog
```

---

## 9. Migration Alignment (Rename Proposal)

The [repo-structure-non-dev.md](../development/proposals/repo-structure-non-dev.md) proposal renames
four directories. Here is how each rename affects each platform:

### 9.1 `commands/` → `prompts/`

| Platform | Impact |
|---|---|
| **Copilot CLI** | `plugin.json` field stays `"commands": [...]` (spec mandated). Script path `commands/` → `prompts/`. Validate and generate scripts updated. |
| **Claude Code** | Slash commands in `.claude/commands/` are unaffected (different path entirely). `claude-plugin.json` field `"slashCommands"` unaffected. |
| **VS Code** | `.github/prompts/` directory is already named `prompts/` — no conflict. Dual-write script reads from `prompts/<name>.md`, writes `.github/prompts/<name>.prompt.md`. |

### 9.2 `mcpServers/` → `tool-connections/`

| Platform | Impact |
|---|---|
| **Copilot CLI** | `plugin.json` field stays `"mcpServers": [...]` (spec mandated). Scripts updated to read from `tool-connections/`. `.mcp.json` filename inside the dir unchanged at the Copilot runtime level. |
| **Claude Code** | `claude-plugin.json` field `"mcpServers"` unaffected (it's the config object, not a directory ref). |
| **VS Code** | `.vscode/mcp.json` generated from `tool-connections/` instead of `mcpServers/`. No end-user impact. |

### 9.3 `.mcp.json` → `connection.json`

| Platform | Impact |
|---|---|
| **Copilot CLI** | Scripts read `connection.json` (source), write `.mcp.json` inside `.copilot-plugin/` (runtime requirement unchanged). |
| **Claude Code** | Generation reads `connection.json` and transforms `servers` → `mcpServers` for `claude-plugin.json`. |
| **VS Code** | Generation reads `connection.json` and writes `.vscode/mcp.json` (format identical, `servers` key). |

### 9.4 `plugins/` → `packages/`

| Platform | Impact |
|---|---|
| **Copilot CLI** | `marketplace.json` `plugins[].source` paths update to `packages/<name>/.copilot-plugin`. CLI install commands unchanged. |
| **Claude Code** | `claude.marketplace.json` `plugins[].source.path` updates to `packages/<name>`. |
| **VS Code** | No direct impact (VS Code doesn't use the packages directory). |

### 9.5 Migration Checklist (Platform-Aware)

#### Filesystem moves
- [ ] `git mv commands prompts`
- [ ] `git mv mcpServers tool-connections`
- [ ] `git mv tool-connections/atlassian/.mcp.json tool-connections/atlassian/connection.json`
- [ ] `git mv plugins packages`

#### Script updates (all three generation scripts)
- [ ] `generate_catalog.py`: `"commands"` dir → `"prompts"`, `"mcpServers"` dir → `"tool-connections"`, `".mcp.json"` → `"connection.json"`, `"plugins"` dir → `"packages"`
- [ ] `validate_catalog.py`: same four path changes
- [ ] `generate_marketplace.py`: `"plugins"` dir → `"packages"`, `"mcpServers"` dir → `"tool-connections"`, `".mcp.json"` source → `"connection.json"` (destination inside `.copilot-plugin/` stays `.mcp.json`)

#### New VS Code artifact scripts (if adding VS Code support)
- [ ] `scripts/generate_vscode_artifacts.py`: reads `tool-connections/*/connection.json`, writes `.vscode/mcp.json`
- [ ] `scripts/generate_vscode_artifacts.py`: reads `prompts/*.md`, writes `.github/prompts/*.prompt.md`

#### New Claude artifact scripts (if adding Claude support)
- [ ] `scripts/generate_claude_marketplace.py`: reads `packages/*/plugin.json` + `tool-connections/*/connection.json`, writes `claude.marketplace.json` + `packages/*/claude-plugin.json`

#### Validation
- [ ] `uv run --script scripts/validate_catalog.py` — 0 errors
- [ ] `uv run --script scripts/generate_catalog.py` — correct `repoPath` values (`packages/...`, `prompts/...`, `tool-connections/...`)
- [ ] `uv run --script scripts/generate_marketplace.py` — `packages/atlassian-mcp/.copilot-plugin/.mcp.json` exists
- [ ] `uv run --with pytest --with pyyaml --with jsonschema --with jinja2 -- pytest -q` — all pass

