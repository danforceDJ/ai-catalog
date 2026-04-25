# Implementation Tasks — Company AI Catalog

> **Derived from:** [User Stories](../userstories/README.md)  
> **Repository:** [danforceDJ/ai-catalog](https://github.com/danforceDJ/ai-catalog)  
> **Date created:** 2026-04-21

Each task maps to one or more user stories. Tasks are ordered by priority (P1 = must-have for a functional catalog, P2 = high-value improvement, P3 = future enhancement).

---

## Current State Summary

The `danforceDJ/ai-catalog` repo already has:

- ✅ Plugin structure: `plugins/<name>/plugin.json` referencing top-level primitives by name list
- ✅ **Flat top-level layout**: standalone `skills/`, `agents/`, `commands/`, `mcpServers/` directories
- ✅ Backward-compatible embedded skill sub-paths inside `plugins/<name>/` still supported
- ✅ Python generator scripts (`generate_catalog.py`, `generate_marketplace.py`, `generate_site.py`)
- ✅ Validation script (`validate_catalog.py`) with secret scanning (now extended to `mcpServers/`)
- ✅ GitHub Actions CI (validate + deploy-site)
- ✅ GitLab CI with bash wrapper scripts
- ✅ Pre-commit hook via `.pre-commit-config.yaml`
- ✅ Web marketplace (GitHub Pages) with bundle badge support
- ✅ Copilot CLI marketplace manifest (`.github/plugin/marketplace.json`)
- ✅ 5 plugins (including `value-stream-1-default` bundle) + 1 template + 3 standalone skills
- ✅ Bundle plugin type detected (`type: "bundle"`) and displayed in marketplace with distinct badge
- ✅ List-reference `plugin.json` validation: missing referenced primitive = hard error

**Gaps vs. user stories and awesome-copilot:**

| Gap | Priority | User Stories |
|---|---|---|
| No `instructions/` type (auto-applied coding standards) | P1 | US-207 |
| No `hooks/` type (agentic session hooks) | P1 | US-208 |
| No scaffolding command for new plugins/skills | P2 | US-402 |
| No `llms.txt` / machine-readable catalog for AI agents | P2 | US-403 |
| Web marketplace lacks category/tag filtering | P2 | US-404 |
| No onboarding cookbook or learning hub equivalent | P3 | US-401 |
| `plugin.json` `type` field inferred, not enforced as enum | P1 | US-501 |
| Drift check between SKILL.md frontmatter and plugin.json is warn-only | P2 | US-301 |
| VS Code deeplink only generated for MCP — not for agent/skill/prompt | P2 | US-103 |
| Top-level standalone skills/agents/commands not installable via Copilot CLI (no plugin wrapper) | P2 | US-102 |

---

## P1 Tasks — Foundation & Correctness

### TASK-101 — Enforce `type` enum in `plugin.json` validation

**User stories:** US-501  
**Files:** `scripts/validate_catalog.py`

**Description:**  
Currently `type` is inferred from which component sub-paths exist. The field is present in `catalog.json` output but not validated against a fixed enum at schema level. This means a typo like `"type": "skilll"` silently passes. Because `plugin.json` exists only for plugins, the enum should be limited to plugin types; templates under `templates/` are out of scope for this field. To avoid changing generation behavior, `plugin.json.type` should be validated as a required consistency check against the type already derived from plugin structure.

**Steps:**
1. Define the valid enum for `plugin.json` as: `["skill", "agent", "prompt", "mcp", "bundle"]`.
2. In `validate_catalog.py`, after loading `plugin.json`, assert `type` is present, is in the enum, and matches the type derived from the plugin's component sub-paths.
3. Add test fixtures that cover both an invalid `type` value and a valid-but-inconsistent declared `type`, and assert validation fails in each case.
4. Run `uv run --with pytest --with pyyaml --with jsonschema --with jinja2 -- pytest -q` — all tests must pass.

**Done when:** `validate_catalog.py` exits non-zero with a clear message if `type` is missing, invalid, or inconsistent with the plugin's derived type.

---

### TASK-102 — Make SKILL.md frontmatter drift a hard error for `name` mismatches

**User stories:** US-301, US-501  
**Files:** `scripts/validate_catalog.py`

**Description:**  
SKILL.md frontmatter `name` and `version` can drift vs. `plugin.json`. The `name` field is especially important — a mismatch means the Copilot CLI installs a skill under the wrong name. Add a `name` drift check and make `name` drift a hard error. Keep `version` drift as a warning.

**Steps:**
1. In `validate_catalog.py`, add a check that compares SKILL.md frontmatter `name` against the expected skill folder name.
2. Treat `name` drift as an `error` (non-zero exit).
3. Keep `version` drift as a warning (version bumping is a common lag).
4. Update the relevant test fixtures to cover `name` drift as a validation failure and `version` drift as a warning-only case.
5. Run full test suite.

**Done when:** Validation exits non-zero if SKILL.md `name` != the skill folder name, while `version` drift remains warning-only.

---

### TASK-103 — Add `author` field to `plugin.json` schema requirements

**User stories:** US-201, US-202, US-203, US-204, US-501  
**Files:** `scripts/validate_catalog.py`, `CONTRIBUTING.md`

**Description:**  
`author` is recommended in CONTRIBUTING.md but not validated. Without it, the marketplace cannot display who built a plugin. Make it a required field with a warning (not error) so existing plugins don't break.

**Steps:**
1. In `validate_catalog.py`, warn if `plugin.json` is missing `author.name`.
2. Add `author` to the example `plugin.json` in `CONTRIBUTING.md`.
3. Update contributor guidance so future plugin submissions include `author.name` rather than implying existing plugins need cleanup.

**Done when:** Missing `author.name` produces a validation warning, and `CONTRIBUTING.md` clearly shows and recommends `author.name` for new plugins.

---

## P1 Tasks — New Content Types

### TASK-201 — Add `instructions/` content type (auto-applied coding standards)

**User stories:** US-207  
**Files:** `scripts/validate_catalog.py`, `scripts/generate_catalog.py`, `scripts/generate_marketplace.py`, `CONTRIBUTING.md`, `instructions/<name>/`

**Description:**  
Modeled after `awesome-copilot`'s `instructions/` folder. Each instruction file is a `.instructions.md` with `applyTo` and `description` frontmatter. Following the new flat top-level layout, instructions live at `instructions/<name>/` in the repo root (not nested inside a plugin folder).

**Steps:**
1. Define the top-level convention: `instructions/<name>/<name>.instructions.md`.
2. Update `validate_catalog.py` to discover and validate instruction files (required: `description`, `applyTo`; filename must match frontmatter `name` if present).
3. Update `generate_catalog.py` to scan `instructions/` and include them in the catalog index.
4. Update `generate_marketplace.py` to expose instructions as raw file install targets.
5. Update `CONTRIBUTING.md` with an "Adding Instructions" section.
6. Create a sample instruction file (e.g., `instructions/typescript-standards/typescript.instructions.md`).
7. Run full test suite.

**Done when:** Instructions appear in `catalog.json`, are installable via Copilot CLI, and validation enforces their schema.

---

### TASK-202 — Add `hooks/` content type (agentic session hooks)

**User stories:** US-208  
**Files:** `scripts/validate_catalog.py`, `scripts/generate_catalog.py`, `CONTRIBUTING.md`, `hooks/<name>/`

**Description:**  
Modeled after `awesome-copilot`'s `hooks/` type. Following the flat top-level layout, hooks live at `hooks/<name>/` in the repo root, each containing a `hooks.json` and a `README.md` with frontmatter.

**Steps:**
1. Define the top-level convention: `hooks/<hook-name>/hooks.json` + `README.md`.
2. Update `validate_catalog.py` to discover hook folders at `hooks/` and validate required fields (`name`, `description` in README.md frontmatter; valid JSON in `hooks.json`).
3. Update `generate_catalog.py` to scan `hooks/` and include hooks in the catalog index.
4. Update `generate_marketplace.py` to expose hook folders as zip-install targets.
5. Update `CONTRIBUTING.md` with an "Adding Hooks" section.
6. Create one sample hook (e.g., `hooks/lint-on-save/`).
7. Run full test suite.

**Done when:** Hook plugins validate, appear in `catalog.json`, and can be installed via CLI.

---

## P2 Tasks — Developer Experience

### TASK-301 — Scaffolding script for new plugins and standalone primitives

**User stories:** US-402  
**Files:** `scripts/scaffold_plugin.py` (new), `CONTRIBUTING.md`

**Description:**  
A `uv`-runnable Python script that creates the boilerplate directory and file structure for a new catalog item. Following the flat top-level layout, standalone skills/agents/commands/MCP configs are scaffolded at their top-level directory; bundle plugins are scaffolded under `plugins/<name>/`. Inspired by `awesome-copilot`'s `npm run plugin:create` and `npm run skill:create` commands.

**Steps:**
1. Create `scripts/scaffold_plugin.py` as a PEP 723 single-file script.
2. Accept `--name <kebab-case-name>` and `--type <skill|agent|prompt|mcp|bundle>` arguments.
3. Generate for standalone types:
   - `skill` → `skills/<name>/SKILL.md` with frontmatter placeholders.
   - `agent` → `agents/<name>.agent.md` with frontmatter placeholders.
   - `prompt` → `commands/<name>.md` with frontmatter placeholders.
   - `mcp` → `mcpServers/<name>/.mcp.json` with `{"servers": {}}` shell.
4. Generate for `bundle`:
   - `plugins/<name>/plugin.json` with `"skills": []`, `"mcpServers": []` placeholders and all required fields.
5. After generation, print the next steps (run validation, fill placeholders, add a plugin wrapper if needed, commit).
6. Add usage instructions to `CONTRIBUTING.md`.
7. Write a test that runs the script and asserts the expected files are created.

**Done when:** `uv run --script scripts/scaffold_plugin.py --name my-skill --type skill` creates `skills/my-skill/SKILL.md` as a valid, validatable skeleton; `--type bundle` creates `plugins/<name>/plugin.json`.

---

### TASK-302 — Generate `llms.txt` for machine-readable catalog discovery

**User stories:** US-403  
**Files:** `scripts/generate_site.py` (or new `scripts/generate_llms.py`), `docs/llms.txt`

**Description:**  
A structured text file (following the [llms.txt standard](https://llmstxt.org/)) listing all catalog items so AI agents can discover them programmatically. Modeled after `awesome-copilot.github.com/llms.txt`.

**Steps:**
1. Add an `llms.txt` generation step to `scripts/generate_site.py` (or create a dedicated script).
2. Format: one section per plugin, with name, type, description, and install command.
3. Publish to `docs/llms.txt` so it is served via GitHub Pages.
4. Add a link to `llms.txt` in `README.md`.
5. Add the generation step to the deploy GitHub Actions workflow.

**Done when:** `docs/llms.txt` is generated at deploy time and linked from `README.md`.

---

### TASK-303 — Add category and tag filtering to the web marketplace

**User stories:** US-404  
**Files:** `scripts/generate_site.py` (or the Jinja template it uses), `docs/index.html` (generated)

**Description:**  
The current marketplace page lists all cards without filtering. Add a category filter bar (buttons or dropdown) and tag chips that filter the visible cards client-side using JavaScript.

**Steps:**
1. Audit existing plugins and ensure all have `category` and `tags` populated in `plugin.json`.
2. In the Jinja/site template, inject the unique category list and tags from `catalog.json`.
3. Add a filter UI: category buttons at the top, tag chips inline on each card.
4. Add JavaScript to show/hide cards based on the active filter.
5. Add a search box that filters by name, description, and tags.
6. Test with at least 3 categories and 6 tags populated.

**Done when:** The deployed marketplace page supports category and tag filtering with no page reload.

---

### TASK-304 — VS Code deeplinks for agent and skill installs

**User stories:** US-103  
**Files:** `scripts/generate_catalog.py`, `scripts/generate_marketplace.py`, `scripts/generate_site.py`

**Description:**  
Currently `vscodeMcpDeeplink` is only generated for MCP plugins. Extend to generate VS Code `chat-agent/install` deeplinks for `.agent.md` files and skill-install deeplinks for skills (following the `awesome-copilot` pattern).

**Steps:**
1. Research the VS Code `vscode:chat-agent/install?url=...` deeplink format (used in `awesome-copilot` README.agents.md).
2. In `generate_catalog.py`, generate `vscodeAgentDeeplink` for plugins with agents.
3. In `generate_catalog.py`, generate `vscodeSkillDeeplink` for plugins with skills (if VS Code supports this).
4. Expose these deeplinks in `catalog.json` and render them as buttons in the marketplace cards.
5. Update `generate_marketplace.py` to include agent deeplinks in the marketplace manifest.

**Done when:** Agent plugins show a "Install in VS Code" button in the marketplace, linking to the correct deeplink.

---

### TASK-305 — Bundle plugin type — explicit marketplace UI treatment ✅ Done

**User stories:** US-206  
**Status:** Completed as part of the flat top-level structure redesign.

- `generate_catalog.py` detects ≥2 component types and emits `type: "bundle"`.
- The site Jinja template renders a `badge-bundle` chip on bundle cards.
- A "Bundles" tab appears in the type-filter bar.
- The reference bundle `plugins/value-stream-1-default/` (skills + MCP) is live in the catalog.

No further action needed.

---

## P2 Tasks — Catalog Content Expansion

### TASK-401 — Add company coding standards as Instructions plugin

**User stories:** US-207  
**Depends on:** TASK-201

**Description:**  
Publish the company's existing coding standards (TypeScript, Python, Java, etc.) as installable instructions. This is the highest-value item for developer productivity — once installed, Copilot automatically applies standards without any prompt engineering.

**Steps:**
1. Identify the top 3 technology stacks used internally (e.g., TypeScript, Python, Java).
2. Create a plugin for each stack (or a single multi-language plugin) with `.instructions.md` files.
3. Each file should cover: naming conventions, import order, error handling, testing patterns.
4. Validate and publish via PR.

**Done when:** At least one coding standards plugin is in the catalog and installable via CLI.

---

### TASK-402 — Add Slack / Teams MCP plugin

**User stories:** US-204  
**Files:** `mcpServers/slack/` (or `mcpServers/teams/`), `plugins/slack-mcp/plugin.json`

**Description:**  
Add MCP server configurations for the company's internal messaging platforms (Slack or Microsoft Teams). Following the flat top-level layout, the MCP config lives at `mcpServers/slack/.mcp.json` and a thin plugin wrapper at `plugins/slack-mcp/plugin.json` makes it installable via Copilot CLI.

**Steps:**
1. Identify the correct MCP server package (e.g., `@modelcontextprotocol/server-slack`).
2. Configure OAuth/SSO — no tokens hard-coded.
3. Create `mcpServers/slack/.mcp.json` with `{"servers": {"slack": {...}}}`.
4. Create `plugins/slack-mcp/plugin.json` with `"mcpServers": ["slack"]`.
5. Test the install flow via `copilot plugin install slack-mcp@ai-catalog`.
6. Validate and publish via PR.

**Done when:** Slack/Teams MCP plugin is in the catalog, uses OAuth, and passes secret scanning.

---

### TASK-403 — Add GitHub MCP plugin

**User stories:** US-204  
**Files:** `mcpServers/github/`, `plugins/github-mcp/plugin.json`

**Description:**  
Add the official GitHub MCP server so developers can use Copilot to query PRs, issues, and repositories programmatically. The MCP config goes in `mcpServers/github/.mcp.json`; a thin wrapper plugin at `plugins/github-mcp/plugin.json` exposes it via Copilot CLI.

**Steps:**
1. Use the official GitHub MCP server (`@github/mcp-server`).
2. Configure with OAuth or GitHub App — no PATs hard-coded.
3. Create `mcpServers/github/.mcp.json` with `{"servers": {"github": {...}}}`.
4. Create `plugins/github-mcp/plugin.json` with `"mcpServers": ["github"]`.
5. Validate and publish.

**Done when:** `copilot plugin install github-mcp@ai-catalog` installs the GitHub MCP server correctly.

---

### TASK-404 — Add code review agent profile

**User stories:** US-202  
**Files:** `agents/code-review.agent.md`, `plugins/code-review-agent/plugin.json`

**Description:**  
A specialized agent profile for code review tasks: checks for security issues, enforces naming conventions, checks test coverage, and summarizes changes in a structured format. Following the flat top-level layout, the agent file lives at `agents/code-review.agent.md`; the plugin wrapper makes it installable via Copilot CLI.

**Steps:**
1. Write `agents/code-review.agent.md` with `tools`, `model`, and `description` frontmatter.
2. Reference relevant company coding standards (link to instructions plugin once TASK-401 is done).
3. Create `plugins/code-review-agent/plugin.json` with `"agents": ["code-review"]`.
4. Validate and publish.

**Done when:** The agent profile is installable and activates in Copilot Chat with the correct persona.

---

## P3 Tasks — Onboarding & Learning

### TASK-501 — Create a Cookbook / Recipe Guide

**User stories:** US-401  
**Files:** `cookbook/README.md`, `cookbook/<recipe>.md`

**Description:**  
Modeled after `awesome-copilot`'s `cookbook/`. Copy-paste-ready recipes for common tasks: "How to create a skill", "How to add an MCP server", "How to write a prompt that chains two tools", etc.

**Steps:**
1. Create `cookbook/README.md` with a table of contents.
2. Write 5 initial recipes covering the most common catalog contribution scenarios.
3. Link from `README.md` and `CONTRIBUTING.md`.

**Done when:** `cookbook/` exists with at least 5 recipes, all linked from the main README.

---

### TASK-502 — Add a Learning Hub to the web marketplace

**User stories:** US-401  
**Depends on:** TASK-302 (site generation improvements)

**Description:**  
A "Getting Started" or "Learning Hub" section on the marketplace page explaining what skills, agents, prompts, and MCP servers are, with links to the relevant CONTRIBUTING.md sections.

**Steps:**
1. Add a "How it works" or "Getting Started" tab/section to the generated `index.html`.
2. Include an explainer for each content type with an install example.
3. Link to `CONTRIBUTING.md` for contributors.

**Done when:** The marketplace page has a visible onboarding section explaining the catalog to new visitors.

---

### TASK-503 — `awesome-copilot` import bridge (opt-in)

**User stories:** US-103, US-206  
**Files:** `scripts/import_awesome_copilot.py` (new, experimental)

**Description:**  
A utility script that reads a subset of `github/awesome-copilot` content (agents, skills) and generates wrapper plugins in the company catalog. This gives developers access to the community collection through the same install interface, subject to a company review gate.

**Steps:**
1. Create `scripts/import_awesome_copilot.py` that fetches and parses the `awesome-copilot` catalog.
2. For each approved external plugin, generate a proxy `plugin.json` pointing to the external raw file URL.
3. Add a review checklist: security scan, license check, responsible AI check.
4. Expose approved external plugins in the marketplace with a clear "External (community)" label.
5. Do **not** commit external secrets or token-requiring configs without review.

**Done when:** At least one curated `awesome-copilot` item is available in the company marketplace via the import bridge.

---

## Tracking

| Task | Priority | User Stories | Status |
|---|---|---|---|
| TASK-101 Enforce `type` enum | P1 | US-501 | ⬜ Todo |
| TASK-102 SKILL.md name drift → error | P1 | US-301, US-501 | ⬜ Todo |
| TASK-103 `author` field warning | P1 | US-201–204, US-501 | ⬜ Todo |
| TASK-201 `instructions/` content type | P1 | US-207 | ⬜ Todo |
| TASK-202 `hooks/` content type | P1 | US-208 | ⬜ Todo |
| TASK-301 Scaffolding script | P2 | US-402 | ⬜ Todo |
| TASK-302 `llms.txt` generation | P2 | US-403 | ⬜ Todo |
| TASK-303 Category/tag filtering in UI | P2 | US-404 | ⬜ Todo |
| TASK-304 VS Code deeplinks for agents/skills | P2 | US-103 | ⬜ Todo |
| TASK-305 Bundle badge in marketplace | P2 | US-206 | ✅ Done |
| TASK-401 Coding standards Instructions plugin | P2 | US-207 | ⬜ Todo |
| TASK-402 Slack/Teams MCP plugin | P2 | US-204 | ⬜ Todo |
| TASK-403 GitHub MCP plugin | P2 | US-204 | ⬜ Todo |
| TASK-404 Code review agent profile | P2 | US-202 | ⬜ Todo |
| TASK-501 Cookbook / Recipe Guide | P3 | US-401 | ⬜ Todo |
| TASK-502 Learning Hub in marketplace | P3 | US-401 | ⬜ Todo |
| TASK-503 awesome-copilot import bridge | P3 | US-103, US-206 | ⬜ Todo |
