# Proposal: Repository Restructure for Non-Developer Accessibility

**Status:** Draft for review  
**Type:** Architecture + Technical Writing  
**Impact:** Non-breaking (all generated outputs remain format-identical)

---

## Executive Summary

The AI Catalog is well-engineered but its structure assumes contributors think like software engineers. A product manager, tech lead, or AI practitioner trying to add their first item today will encounter camelCase directory names that don't explain themselves, hidden dot-files invisible in Finder, an unexplained two-file requirement to publish a single skill, and no in-folder guidance anywhere.

This proposal fixes all of that through:
1. **Four targeted directory/file renames** — plain English names that match how non-developers think
2. **A README in every content directory** — contextual help wherever someone lands
3. **Six step-by-step contribution guides** — one per content type, no developer assumptions
4. **A migration checklist** — exact steps for the implementing engineer, with every affected script line identified

Every machine-readable output (`catalog.json`, `marketplace.json`) remains format-identical after the changes.

---

## Table of Contents

1. [Current Pain Points](#1-current-pain-points)
2. [Mental Model Gap](#2-mental-model-gap)
3. [Proposed Repository Structure](#3-proposed-repository-structure)
4. [Key Renames and Rationale](#4-key-renames-and-rationale)
5. [README Content for Every Content Directory](#5-readme-content-for-every-content-directory)
6. [Step-by-Step Guides for Non-Developers](#6-step-by-step-guides-for-non-developers)
7. [Migration Notes](#7-migration-notes)
8. [Machine-Readable Outputs After Migration](#8-machine-readable-outputs-after-migration)
9. [Recommended Additional Changes](#9-recommended-additional-changes)
10. [Migration Checklist](#10-migration-checklist)

---

## 1. Current Pain Points

### 1.1 The Invisible Two-Tier Model

Adding a skill requires files in **two separate places**: `skills/<name>/SKILL.md` (the content) and `plugins/<name>/plugin.json` (the installer). There is no in-repo explanation of why this split exists. A non-developer puts the file in `skills/` and considers themselves done — not knowing that without the matching `plugin.json`, the item won't be installable.

**Example:** Adding a GitHub code review skill requires:
1. `skills/github-code-review/SKILL.md` — with a strict YAML frontmatter block
2. `plugins/github-code-review/plugin.json` — with `"skills": ["github-code-review"]`

Step 2 is only mentioned in `CONTRIBUTING.md`, which uses terms like "wrapper," "primitive," and "name list reference style."

### 1.2 `mcpServers` Directory Name

`mcpServers` is camelCase in an otherwise kebab-case repository. The term "MCP server" requires knowing what the Model Context Protocol is. A non-developer's mental model for "where do I put a new tool connection?" is not "`mcpServers/`."

### 1.3 Hidden `.mcp.json` Files

`mcpServers/atlassian/.mcp.json` starts with a dot — **hidden by default** in macOS Finder, Windows Explorer, and most file managers. A non-developer browsing the folder sees an empty directory. There is no technical reason for the dot prefix; it is a convention borrowed from `.vscode/mcp.json` that does not apply here.

### 1.4 `commands/` Directory Name

The directory holds prompt templates for AI slash commands, not CLI commands. A product manager thinking "I want to add a prompt for the team" will not look in `commands/`. The correct human-facing label is already used in the installer (type `"prompt"`) — it should be the directory name too.

### 1.5 ALL CAPS Filenames Without Explanation

`SKILL.md`, `TEMPLATE.md` — these conventions come from external standards but appear arbitrary and intimidating. No README alongside these files explains why they are caps or what fields are mandatory.

### 1.6 YAML Frontmatter Is a Developer Concept

Every content file begins with a structured YAML header between `---` delimiters. Non-developers writing Markdown don't use frontmatter. The rules are strict, enforced by CI, but never explained near the files — only in `specs/catalog-items.md`, a file addressed to LLMs.

### 1.7 No In-Folder Guidance Anywhere

Not one of the content directories — `skills/`, `agents/`, `commands/`, `mcpServers/`, `templates/`, `plugins/` — contains a `README.md`. All help is in `CONTRIBUTING.md`, which requires scrolling past unrelated sections.

### 1.8 Tooling Requires Developer Setup

`CONTRIBUTING.md` opens with "Install the pre-commit hooks." The PR workflow doesn't make clear that `catalog.json` and `marketplace.json` must be committed or CI fails.

### 1.9 Naming Rules Are Not Co-Located with Content

The kebab-case rule, ≤64-char limit, and "filename stem must equal `name` field" rule are only documented in `CONTRIBUTING.md` and `specs/README.md`. A contributor naming their file `My New Skill.md` discovers the error only when CI fails.

### 1.10 "Plugin" Terminology Mismatch

`plugins/` means a specific thing (a Copilot CLI installable package), but "plugin" in everyday usage means any extension. Non-developers conflate "the repo has plugins" with "everything in the repo is a plugin."

---

## 2. Mental Model Gap

| What a non-developer expects | What the repo actually requires |
|---|---|
| "I add a file to the right folder and it's done." | Add a primitive file **and** create a `plugin.json` wrapper. |
| "Folder names describe what's inside in plain English." | `mcpServers` (camelCase acronym), `commands` (means CLI, not prompts). |
| "I can see all files when I browse the folder." | `.mcp.json` and `.copilot-plugin/` are hidden from Finder/Explorer. |
| "I write a Markdown file with my content." | Markdown must begin with a structured YAML header block. |
| "The folder has a README telling me what to do here." | No README exists in any content directory. |
| "I commit and open a PR." | Must also regenerate two tracked artifact files, or CI fails. |

---

## 3. Proposed Repository Structure

**Goals:** Every directory name is self-describing plain English. Every directory has a README. The two-tier model is explained at the point of use. Machine-readable outputs are unchanged.

```
ai-catalog/
│
├── 📖 README.md                          updated: plain-English orientation
├── 📖 CONTRIBUTING.md                    updated: non-dev-first
├── 🤖 AGENTS.md                          unchanged
├── ⚙️  marketplace.config.json            unchanged
├── 📦 catalog.json                       unchanged: generated search index (tracked)
│
│   ── Content directories ──
│
├── 🧠 skills/                            unchanged name; + README added
│   ├── 📖 README.md                      NEW
│   ├── jira-ticket-from-code/
│   │   └── SKILL.md
│   ├── generate-architecture-doc/
│   │   └── SKILL.md
│   └── publish-to-confluence/
│       └── SKILL.md
│
├── 🤖 agents/                            unchanged name; + README added
│   ├── 📖 README.md                      NEW
│   └── default.agent.md
│
├── 💬 prompts/                           RENAMED from: commands/
│   ├── 📖 README.md                      NEW
│   └── pr-description.md
│
├── 🔌 tool-connections/                  RENAMED from: mcpServers/
│   ├── 📖 README.md                      NEW
│   └── atlassian/
│       └── connection.json               RENAMED from: .mcp.json (identical format, now visible)
│
├── 📄 templates/                         unchanged name; + README added
│   ├── 📖 README.md                      NEW
│   └── solution-architecture/
│       └── TEMPLATE.md
│
├── 📦 packages/                          RENAMED from: plugins/
│   ├── 📖 README.md                      NEW
│   ├── atlassian-mcp/
│   │   ├── plugin.json                   unchanged: Copilot CLI spec mandates this filename
│   │   └── .copilot-plugin/              auto-generated, gitignored
│   ├── default-agent/
│   │   └── plugin.json
│   ├── jira-ticket-from-code/
│   │   └── plugin.json
│   ├── pr-description-prompt/
│   │   └── plugin.json
│   └── value-stream-1-default/
│       └── plugin.json
│
│   ── Infrastructure (developer-facing, unchanged) ──
│
├── ⚙️  scripts/
├── 📐 specs/
├── 🧪 tests/
├── 🔧 .github/
└── development/
    └── proposals/
        └── repo-structure-non-dev.md     ← this file
```

### Plain-English Directory Descriptions

| Directory | What it is |
|---|---|
| `skills/` | Teaching packages for your AI assistant — how to do specific tasks like creating a Jira ticket or writing an architecture doc. |
| `agents/` | Personality and behavior profiles — standing rules the AI always follows (commit conventions, security policies, available tools). |
| `prompts/` | Reusable prompt templates that appear as slash commands (`/pr-description`, `/write-adr`) in AI coding tools. |
| `tool-connections/` | Configuration files that connect the AI to external services — Jira, Confluence, GitHub, Slack. |
| `templates/` | Pre-structured Markdown scaffolds teams can download and fill in (architecture docs, ADRs, runbooks). |
| `packages/` | Installable bundles for GitHub Copilot CLI. Think of these as "the installer" for content in the other folders. |

---

## 4. Key Renames and Rationale

### 4.1 `commands/` → `prompts/`

**Rationale:** Contents are prompt templates for AI slash commands, not CLI commands. The `catalog.json` type field is already `"prompt"` — the directory should match. The `plugin.json` manifest field stays `"commands": [...]` (Copilot CLI spec) — only the filesystem path changes.

**Script changes required:**

| File | Old string | New string |
|---|---|---|
| `generate_catalog.py` | `/ "commands"` (path) | `/ "prompts"` |
| `generate_catalog.py` | `"repoPath": "commands"` | `"repoPath": "prompts"` |
| `validate_catalog.py` | `/ "commands"` (path) | `/ "prompts"` |

### 4.2 `mcpServers/` → `tool-connections/`

**Rationale:** `mcpServers` is camelCase (inconsistent), uses an unexplained acronym, and describes the implementation mechanism not the user benefit. "Tool connections" is plain English explaining what's inside. The JSON field `"mcpServers": [...]` in `plugin.json` is unchanged (Copilot CLI spec) — only the filesystem directory name changes.

**Script changes required:**

| File | Old string | New string |
|---|---|---|
| `generate_catalog.py` | `/ "mcpServers"` (path) | `/ "tool-connections"` |
| `validate_catalog.py` | `/ "mcpServers"` (path) | `/ "tool-connections"` |
| `generate_marketplace.py` | `"mcpServers"` dir references | `"tool-connections"` |

### 4.3 `.mcp.json` → `connection.json`

**Rationale:** Dot-prefix files are hidden by default in macOS Finder and Windows Explorer. A non-developer sees an empty folder. `connection.json` is visible, descriptive, and self-explanatory. The JSON content format is **identical**. 

**Important:** The **generated** file inside `.copilot-plugin/` packages must remain `.mcp.json` (Copilot CLI runtime requirement). The materialization step in `generate_marketplace.py` reads `connection.json` (source) and writes `.mcp.json` (destination inside the generated package).

**Script changes required:**

| File | Old | New |
|---|---|---|
| `generate_catalog.py` | `/ ".mcp.json"` (source path) | `/ "connection.json"` |
| `validate_catalog.py` | `/ ".mcp.json"` (source path) | `/ "connection.json"` |
| `generate_marketplace.py` | source: `/ ".mcp.json"` | `/ "connection.json"` (copy target inside `.copilot-plugin/` stays `.mcp.json`) |

### 4.4 `plugins/` → `packages/`

**Rationale:** "Plugin" is overloaded — non-developers think the entire catalog is "plugins." The sub-meanings (wrapper plugin vs. bundle plugin) are never plain-English explained. "Package" clearly means "installable unit" without implying everything else is not an extension. The file inside (`plugin.json`) must keep its name — mandated by the Copilot CLI spec.

**Script changes required:**

| File | Old | New |
|---|---|---|
| `generate_catalog.py` | `/ "plugins"` (dir) | `/ "packages"` |
| `generate_catalog.py` | `"repoPath": f"plugins/..."` | `f"packages/..."` |
| `validate_catalog.py` | `/ "plugins"` (dir) | `/ "packages"` |
| `generate_marketplace.py` | all `plugins/<name>/` paths | `packages/<name>/` |

---

## 5. README Content for Every Content Directory

### `skills/README.md`

```markdown
# Skills

A **skill** teaches your AI assistant how to do a specific, repeatable task — like creating a
Jira ticket from a code comment, or publishing a document to Confluence.

## Folder structure

```
skills/
└── your-skill-name/
    └── SKILL.md    ← the skill definition (UPPERCASE filename is required by the standard)
```

## How to add a skill

1. **Create a folder:** `skills/your-skill-name/`  
   Use lowercase words separated by hyphens. Example: `generate-meeting-notes`

2. **Create `SKILL.md`** — copy this starter and fill it in:

```markdown
---
name: your-skill-name
description: One sentence describing what this skill does.
version: 1.0.0
license: MIT
compatibility: Works standalone. Requires Atlassian MCP for Jira/Confluence steps.
metadata:
  author: your-team-name
  tags: ["tag1", "tag2"]
---

# Your Skill Name

## Instructions

1. First step the AI should follow.
2. Second step — be as concrete as possible.

## Example

**Input:** What the user asks or provides.
**Output:** What the AI produces.
```

3. **Make it installable** (optional): follow the guide in [`../packages/README.md`](../packages/README.md).

## Naming rules

- Folder name: lowercase, hyphens only, no spaces, ≤ 64 characters
- The `name:` field in `SKILL.md` must match the folder name exactly
- ✅ `generate-meeting-notes` / `name: generate-meeting-notes`
- ❌ `GenerateMeetingNotes` — this will fail CI validation
```

---

### `agents/README.md`

```markdown
# Agent Profiles

An **agent profile** sets the standing rules your AI assistant follows across your entire
environment — coding standards, git habits, security policies, which tools are available.
Unlike skills (specific tasks), an agent profile is always active in the background.

## Folder structure

```
agents/
└── your-profile-name.agent.md
```

## How to add an agent profile

1. **Create a file:** `agents/your-profile-name.agent.md`  
   Filename: lowercase, hyphens, ends in `.agent.md` exactly.

2. **Copy this starter:**

```markdown
---
name: your-profile-name
description: One sentence: who is this for and what does it enforce?
---

# Profile Name

## General Rules

- Rule 1 the AI always follows.

## Git Workflow

- Use conventional commits (feat:, fix:, chore:)
- Never commit directly to `main`

## Security

- Never commit secrets or credentials.

## Available Tools and Skills

- `atlassian` — Jira and Confluence via Atlassian MCP
- `jira-ticket-from-code` — create Jira tickets from code comments
```

3. The `name:` field must match the filename stem exactly:  
   File `backend-team.agent.md` → `name: backend-team`

4. **Make it installable** (optional): follow [`../packages/README.md`](../packages/README.md).
```

---

### `prompts/README.md`

```markdown
# Prompts (Slash Commands)

A **prompt** is a reusable template that appears as a slash command in AI coding assistants —
like `/pr-description`, `/write-adr`, `/summarize-pr`. Write it once here; every team member
gets it as a command.

> **Note for engineers:** The `plugin.json` manifest field for prompts is still `"commands": [...]`
> (Copilot CLI spec requirement). Only this directory is named `prompts/`.

## Folder structure

```
prompts/
└── your-prompt-name.md    ← filename becomes the slash command name
```

## How to add a prompt

1. **Create a file:** `prompts/your-prompt-name.md`  
   The filename (without `.md`) becomes the slash command. Example: `write-standup.md` → `/write-standup`

2. **Copy this starter:**

```markdown
---
name: your-prompt-name
description: One sentence: what does this prompt help with?
---

Write your prompt template here. Use HTML comments as placeholder instructions.

## Section One

<!-- What goes here? -->

-

## Section Two

- [ ] Item
```

3. **Critical naming rule:** The `name:` field **must exactly match** the filename stem.  
   ✅ File `write-standup.md` → `name: write-standup`  
   ❌ File `write-standup.md` → `name: WriteStandup` → CI fails

4. **Make it installable** (optional): follow [`../packages/README.md`](../packages/README.md).
```

---

### `tool-connections/README.md`

```markdown
# Tool Connections

A **tool connection** is a configuration file that lets your AI assistant connect to an external
service — Jira, Confluence, GitHub, Slack — and take actions there directly.

Technically these are [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server
configs, but you don't need to know MCP to add one.

## Folder structure

```
tool-connections/
└── your-tool-name/
    └── connection.json    ← the connection configuration
```

## How to add a tool connection

1. **Find your tool's MCP endpoint.** Common ones:
   - Atlassian (Jira/Confluence): `https://mcp.atlassian.com/v1/sse`
   - GitHub: see GitHub Copilot MCP documentation
   - Check your tool's developer docs for "MCP server"

2. **Create a folder:** `tool-connections/your-tool-name/`

3. **Create `connection.json`** — copy and edit:

```json
{
  "servers": {
    "your-tool-name": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://your-tool-endpoint-url"]
    }
  }
}
```

4. **Security:** Never put passwords, tokens, or API keys in this file. Use OAuth or SSO flows
   only. The repository runs automatic secret scanning — hardcoded credentials will block your PR.

5. **Make it installable** (optional): follow [`../packages/README.md`](../packages/README.md).

## Naming rules

- Folder name: lowercase, hyphens only (e.g., `atlassian`, `github-enterprise`)
- The server key inside `connection.json` should match the folder name
```

---

### `templates/README.md`

```markdown
# Document Templates

A **document template** is a pre-structured Markdown scaffold teams can download and fill in:
architecture documents, ADRs, runbooks, incident reports, team charters, etc.

Templates are web-only — they appear in the [catalog](https://danforceDJ.github.io/ai-catalog/)
with Copy and Download buttons, but cannot be installed via `copilot plugin install`.

## Folder structure

```
templates/
└── your-template-name/
    └── TEMPLATE.md    ← the document scaffold (UPPERCASE filename is required)
```

## How to add a template

1. **Create a folder:** `templates/your-template-name/`

2. **Create `TEMPLATE.md`** — copy this starter:

```markdown
---
name: your-template-name
description: One sentence describing what document this template produces.
version: 1.0.0
category: architecture
tags: [docs, architecture]
keywords: [design, document]
---

# Document Title: <Project Name>

## Section One

<!-- Fill in: context and purpose -->

## Section Two

- Item one
- Item two
```

3. Replace example sections with your actual document structure.

## Required fields (all four must be present)

`name`, `description`, `version`, `category`

## Category examples

`architecture`, `process`, `engineering`, `planning` — or any consistent custom label.
```

---

### `packages/README.md`

```markdown
# Packages

A **package** wraps one or more catalog items into a single installable unit. Once created,
anyone can run:

```bash
copilot plugin install your-package-name@ai-catalog
```

You only need a package if you want that one-liner install. Items in `skills/`, `agents/`,
`prompts/`, and `tool-connections/` always appear in the web catalog regardless.

## Folder structure

```
packages/
└── your-package-name/
    └── plugin.json          ← package manifest (filename is fixed by Copilot CLI spec)
    └── .copilot-plugin/     ← auto-generated, do not edit
```

## How to create a package

> **Prerequisite:** The items you want to package must already exist in their folders.

1. **Create a folder:** `packages/your-package-name/`  
   Name rules: lowercase, hyphens only, ≤ 64 characters.

2. **Create `plugin.json`** — pick the template for your content type:

**Skill package:**
```json
{
  "name": "your-package-name",
  "description": "What this installs.",
  "version": "1.0.0",
  "author": {"name": "your-name"},
  "license": "MIT",
  "keywords": ["keyword1"],
  "category": "productivity",
  "skills": ["skill-folder-name"]
}
```

**Agent package:**
```json
{
  "name": "your-package-name",
  "description": "What this installs.",
  "version": "1.0.0",
  "author": {"name": "your-name"},
  "license": "MIT",
  "category": "agents",
  "agents": ["agent-name"]
}
```

**Prompt package:**
```json
{
  "name": "your-package-name",
  "description": "What this installs.",
  "version": "1.0.0",
  "author": {"name": "your-name"},
  "license": "MIT",
  "category": "prompts",
  "commands": ["prompt-file-name"]
}
```
> Note: the field is `"commands"` even though the directory is `prompts/` — this is a Copilot CLI spec requirement.

**Tool connection package:**
```json
{
  "name": "your-package-name",
  "description": "What this installs.",
  "version": "1.0.0",
  "author": {"name": "your-name"},
  "license": "MIT",
  "category": "integrations",
  "mcpServers": ["tool-connection-folder-name"]
}
```

**Bundle (multiple types):** combine keys as needed.

3. The `"name"` field must exactly match the folder name.  
4. Do not edit the `.copilot-plugin/` directory — it is auto-generated.
5. Open a pull request — CI validates and publishes everything automatically.
```

---

## 6. Step-by-Step Guides for Non-Developers

### Guide A: Add a Tool Connection + Package

**Goal:** AI assistant can connect to an external service AND colleagues can install it with one command.

1. Find your tool's MCP endpoint URL (check the tool's developer docs for "MCP server")
2. Create `tool-connections/<tool-name>/connection.json` — copy the starter from `tool-connections/README.md`
3. Create `packages/<tool-name>-mcp/plugin.json` — use the tool connection package template from `packages/README.md`
4. Open a pull request — CI validates and generates install artifacts automatically

**Never put passwords or tokens in `connection.json`.** Use OAuth/SSO flows only.

---

### Guide B: Add a Skill

**Goal:** Teach the AI a new repeatable task for team use.

1. Create `skills/<skill-name>/SKILL.md` — copy starter from `skills/README.md`
2. *(Optional)* Create `packages/<skill-name>/plugin.json` to enable `copilot plugin install`
3. Open a pull request

Without the package, the skill still appears in the web catalog with Copy and Download buttons.

---

### Guide C: Add an Agent Profile

**Goal:** Set standing behavioral rules for the AI (conventions, security policies, available tools).

1. Create `agents/<profile-name>.agent.md` — copy starter from `agents/README.md`
2. *(Optional)* Create `packages/<profile-name>-agent/plugin.json`
3. Open a pull request

---

### Guide D: Add a Prompt Template (Slash Command)

**Goal:** Create a reusable prompt that appears as a slash command (`/your-command`) in AI tools.

1. Create `prompts/<prompt-name>.md` — the filename becomes the slash command name
2. Copy starter from `prompts/README.md`
3. Ensure `name:` field exactly matches the filename stem (CI enforces this)
4. *(Optional)* Create `packages/<prompt-name>-prompt/plugin.json`
5. Open a pull request

---

### Guide E: Add a Document Template

**Goal:** Provide a reusable document structure teams can download.

1. Create `templates/<template-name>/TEMPLATE.md`
2. Copy starter from `templates/README.md`
3. Ensure all four required fields are in the header: `name`, `description`, `version`, `category`
4. Open a pull request

Templates appear in the web catalog automatically — no package needed.

---

### Guide F: Add a Bundle (Multiple Items in One Package)

**Goal:** Let a team install everything they need for a workflow in one command.

**Prerequisite:** All skills, agents, prompts, and tool connections you want to bundle must already exist in their directories.

1. Create `packages/<bundle-name>/plugin.json`
2. Reference all items using their respective folder names:

```json
{
  "name": "my-team-bundle",
  "description": "Complete setup for My Team: Jira, Confluence, and PR description command.",
  "version": "1.0.0",
  "author": {"name": "my-team"},
  "license": "MIT",
  "category": "bundles",
  "skills": ["jira-ticket-from-code", "publish-to-confluence"],
  "commands": ["pr-description"],
  "mcpServers": ["atlassian"]
}
```

3. Open a pull request

---

## 7. Migration Notes

### What changes for content

| Before | After | Action |
|---|---|---|
| `commands/<name>.md` | `prompts/<name>.md` | `git mv commands prompts` |
| `mcpServers/<name>/.mcp.json` | `tool-connections/<name>/connection.json` | `git mv mcpServers tool-connections` then rename file |
| `plugins/<name>/plugin.json` | `packages/<name>/plugin.json` | `git mv plugins packages` |
| No content directory READMEs | README in every content directory | Create 6 new README files |

### What does NOT change

- All file **formats** — `plugin.json`, `SKILL.md`, `TEMPLATE.md`, `connection.json` content is identical to old `.mcp.json`
- `catalog.json` output structure — field names, nesting, values
- `.github/plugin/marketplace.json` output structure
- Copilot CLI install commands — `copilot plugin install <name>@ai-catalog` unchanged
- `plugin.json` JSON field names — `"mcpServers"`, `"commands"` stay because they are Copilot CLI spec fields
- `.copilot-plugin/` generated packages — internal format unchanged; the file inside is still `.mcp.json` (runtime requirement)

### Script changes: search-and-replace summary

| Old path literal | New path literal | Affected scripts |
|---|---|---|
| `"commands"` (filesystem) | `"prompts"` | `generate_catalog.py`, `validate_catalog.py` |
| `"mcpServers"` (filesystem dir) | `"tool-connections"` | all three generation scripts |
| `".mcp.json"` (source file) | `"connection.json"` | all three generation scripts |
| `"plugins"` (filesystem dir) | `"packages"` | all three generation scripts |

**Key distinction:** `"mcpServers"` and `"commands"` as **JSON keys** in `plugin.json` are NOT changed. Only filesystem path strings in the scripts change.

**Materialization detail in `generate_marketplace.py`:** reads `tool-connections/<name>/connection.json` (source) and writes `.copilot-plugin/.mcp.json` (destination) — the copy source filename changes, the copy destination filename stays `.mcp.json`.

### Backward compatibility for users

Existing `copilot plugin install` commands are unaffected. The marketplace install commands are driven by `.github/plugin/marketplace.json`, which is regenerated after migration and points to `packages/<name>/.copilot-plugin/`. **No change to any user-facing command.**

---

## 8. Machine-Readable Outputs After Migration

### `catalog.json` — format identical

```
packages/<name>/plugin.json  →  catalog entry (type derived from components)
skills/<name>/SKILL.md       →  standalone catalog entry, type: "skill"
agents/<name>.agent.md       →  standalone catalog entry, type: "agent"
prompts/<name>.md            →  standalone catalog entry, type: "prompt"
tool-connections/<name>/connection.json  →  MCP component data
templates/<name>/TEMPLATE.md →  template catalog entry
```

### `.github/plugin/marketplace.json` — format identical

`source` paths update to `packages/<name>/.copilot-plugin/` — consumers (Copilot CLI) are unaffected.

### End-to-end flow after migration

```
Contributor adds:
  skills/github-code-review/SKILL.md
  packages/github-code-review/plugin.json

      ↓  (pre-commit hook or CI)

generate_catalog.py     → catalog.json (unchanged format)
generate_marketplace.py → packages/github-code-review/.copilot-plugin/
                        → .github/plugin/marketplace.json (unchanged format)

      ↓  (on merge to main)

generate_site.py  → docs/index.html
generate_zips.py  → docs/dl/github-code-review.zip

      ↓

GitHub Pages + Copilot CLI — unchanged user experience
```

---

## 9. Recommended Additional Changes

These are not required for the rename migration but complete the non-developer accessibility goal:

### 9.1 Rewrite `CONTRIBUTING.md` — Non-Developer Track First

Restructure into two tracks:
- **Track 1:** "Add content via pull request" — links to the six guides in Section 6; no setup required
- **Track 2:** "Local development setup" — `uv`, pre-commit hooks, script details — moved to the bottom

### 9.2 Add a Scaffolding Script

`scripts/scaffold.sh skill github-code-review` creates the correct folder and `SKILL.md` with filled-in placeholders. Already identified as missing in `specs/gaps.md`. Highest single DX improvement after the renames.

### 9.3 Document the `"commands"` JSON Key vs `prompts/` Directory Explicitly

Add a callout in `packages/README.md` and `CONTRIBUTING.md`: "The `plugin.json` field is `"commands": [...]` even though the directory is `prompts/` — this is a Copilot CLI spec requirement that cannot be changed."

### 9.4 Fix the Duplicate `atlassian` Catalog Entry

`tool-connections/atlassian/` emits a standalone catalog entry with empty metadata alongside the `atlassian-mcp` package card. Fix: either add metadata to `connection.json` or update `generate_catalog.py` to suppress standalone entries fully covered by a package. (See `specs/gaps.md` P1.)

### 9.5 Improve CI Error Messages for Naming Violations

Change `"name 'MySkill' is not kebab-case"` to `"name 'MySkill' is not kebab-case — suggestion: 'my-skill'"`. Non-developers need actionable feedback, not just the rule violated.

---

## 10. Migration Checklist

For the engineer executing this migration:

### Filesystem moves

- [ ] `git mv commands prompts`
- [ ] `git mv mcpServers tool-connections`
- [ ] `git mv tool-connections/atlassian/.mcp.json tool-connections/atlassian/connection.json`
- [ ] `git mv plugins packages`

### Script updates — `generate_catalog.py`

- [ ] `"commands"` directory path → `"prompts"`
- [ ] `"repoPath": "commands"` → `"repoPath": "prompts"`
- [ ] `"mcpServers"` directory path → `"tool-connections"`
- [ ] `".mcp.json"` source filename → `"connection.json"`
- [ ] `"plugins"` directory path → `"packages"`
- [ ] `"repoPath": f"plugins/..."` → `f"packages/..."`
- [ ] `"repoPath": f"mcpServers/..."` → `f"tool-connections/..."`

### Script updates — `validate_catalog.py`

- [ ] `"commands"` directory path → `"prompts"`
- [ ] `"mcpServers"` directory path → `"tool-connections"`
- [ ] `".mcp.json"` path → `"connection.json"`
- [ ] `"plugins"` directory path → `"packages"`

### Script updates — `generate_marketplace.py`

- [ ] `"mcpServers"` directory path → `"tool-connections"`
- [ ] Source: `".mcp.json"` → `"connection.json"` (copy source)
- [ ] Destination inside `.copilot-plugin/`: keep as `.mcp.json` (do NOT change)
- [ ] `"plugins"` directory path → `"packages"`

### Script updates — `generate_zips.py`

- [ ] `"plugins"` directory path → `"packages"` (if hardcoded)

### Test fixtures — `tests/`

- [ ] Update all path literals referencing `plugins/`, `commands/`, `mcpServers/`, `.mcp.json`

### New files — content directory READMEs

- [ ] `skills/README.md` (content from Section 5.1)
- [ ] `agents/README.md` (content from Section 5.2)
- [ ] `prompts/README.md` (content from Section 5.3)
- [ ] `tool-connections/README.md` (content from Section 5.4)
- [ ] `templates/README.md` (content from Section 5.5)
- [ ] `packages/README.md` (content from Section 5.6)

### Documentation updates

- [ ] Root `README.md` — directory tree diagram
- [ ] `CONTRIBUTING.md` — restructure with non-dev track first; update all paths
- [ ] `specs/architecture.md` — directory tree + path references
- [ ] `specs/catalog-contents.md` — file paths for all current items
- [ ] `specs/catalog-items.md` — path patterns in type schemas
- [ ] `specs/scripts.md` — input/output paths

### Validation

- [ ] `uv run --script scripts/generate_catalog.py` — completes without error
- [ ] `uv run --script scripts/generate_marketplace.py` — completes without error
- [ ] `uv run --script scripts/validate_catalog.py` — 0 errors
- [ ] `uv run --with pytest --with pyyaml --with jsonschema --with jinja2 -- pytest -q` — all pass
- [ ] Spot-check: regenerated `catalog.json` has correct `"repoPath"` values
- [ ] Spot-check: `packages/atlassian-mcp/.copilot-plugin/.mcp.json` exists and is valid JSON
- [ ] Spot-check: `copilot plugin install` against regenerated `marketplace.json` resolves correctly

---

*End of proposal.*

