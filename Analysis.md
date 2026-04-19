# AI Catalog Repository — Analysis Report & Task Backlog

**Repository:** [danforceDJ/ai-catalog](https://github.com/danforceDJ/ai-catalog)
**Date:** 2026-04-19
**Analyst:** Claude (Anthropic)

---

## 1. Executive Summary

The repository provides a solid foundation for a company-wide AI configuration marketplace. Core auto-discovery, catalog generation, and static site publishing work correctly. However, several critical features required to meet the stated goal — *one-click install to global user configuration from the marketplace page* — are entirely absent. Additionally, CI validation, GitLab support, and template handling are missing.

---

## 2. Architecture Overview

The system is built on three open standards:

- **AGENTS.md** — agent behaviour instructions
- **Agent Skills / SKILL.md** — reusable skill packages with YAML frontmatter
- **Model Context Protocol (MCP)** — server configuration packages

The pipeline flow is:

```
filesystem conventions
        ↓
generate-catalog.sh  →  catalog.json
        ↓
generate-site.sh     →  docs/index.html
        ↓
GitHub Actions       →  GitHub Pages (docs/)
```

---

## 3. What Works

| Area | Status | Notes |
|---|---|---|
| Filesystem auto-discovery | ✅ Works | `find` + `sort -z` is solid |
| VSCode project-level MCP install | ✅ Works | `jq -s` merge is correct |
| Skill frontmatter parsing | ✅ Works | YAML fields parsed reliably |
| Static site design | ✅ Works | Clean, readable card layout |
| CI concurrency guard | ✅ Works | Prevents race on rapid pushes |
| CONTRIBUTING / AGENTS.md conventions | ✅ Works | Clear naming and structure rules |

---

## 4. Gap Analysis

### 4.1 🔴 Critical — Missing Features

#### GAP-01: Global user-level install does not exist

`install.sh` only installs into a `--project` path (defaulting to `$(pwd)`). There is no `--global` flag and no logic to write to user-level configuration directories:

- **VSCode** (1.99+): `~/.config/Code/User/mcp.json` (Linux), `~/Library/Application Support/Code/User/mcp.json` (macOS), `%APPDATA%\Code\User\mcp.json` (Windows)
- **JetBrains**: `~/.config/JetBrains/<IDE>/mcp.json` (Linux), `~/Library/Application Support/JetBrains/<IDE>/mcp.json` (macOS), `%APPDATA%\JetBrains\<IDE>\mcp.json` (Windows)
- **Skills / Agent Profiles**: No global equivalent exists yet — needs a convention to be defined (e.g. `~/.ai-catalog/skills/`)

Without this, the marketplace "install" buttons cannot deliver on the stated goal.

#### GAP-02: Marketplace install buttons do nothing

The `<code class="oneliner">` blocks in `docs/index.html` are static display text. There is no:

- Copy-to-clipboard button
- `vscode://` deep-link URI handler
- Custom `aicatalog://` protocol handler
- Any API or backend endpoint

A user visiting the GitHub Pages site cannot trigger any install action. The UX implies one-click install but requires manual copy-paste.

#### GAP-03: No catalog validation in CI

`generate-catalog.sh` runs but its output is never validated before publishing. Currently undetected failure modes include:

- Empty `name` or `description` fields
- `path` entries that point to non-existent files
- `SKILL.md` files with missing required frontmatter fields (`name`, `description`, `version`)
- `vscode.mcp.json` files that are invalid JSON or lack a `servers` key
- `AGENTS.md` files that are empty

#### GAP-04: No pull request / merge request validation pipeline

There is only a push-to-`main` pipeline. No separate workflow validates catalog items on PRs before they are merged. A broken or incomplete contribution ships silently.

#### GAP-05: Templates are not implemented

The stated goal includes templates as a catalog type. There is no `templates/` directory, no discovery logic in `generate-catalog.sh`, no install handling in `install.sh`, and no section in the marketplace page.

---

### 4.2 🟡 Architectural Issues

#### ARCH-01: Agent description extraction is broken

`generate-catalog.sh` extracts agent descriptions with:

```bash
awk 'NF && $0 !~ /^#/ {print; exit}' "$agent_md"
```

This grabs the first non-empty, non-heading line of the file body, which for `agents/default/AGENTS.md` resolves to `- Follow the existing code style and project conventions.` — a raw bullet point from the `## General Rules` section body. The correct approach is to add YAML frontmatter to `AGENTS.md` files (matching the pattern already used for `SKILL.md`) and parse from there.

#### ARCH-02: Shell-generates-HTML is fragile at scale

`generate-site.sh` uses shell string interpolation to emit HTML. This works for three items but will produce malformed or XSS-vulnerable output as the catalog grows, because descriptions may contain `<`, `>`, `&`, `"`, backticks, or newlines. The existing `sed 's/"/\\"/g'` band-aid in `generate-catalog.sh` does not cover all cases. The site generator should use a proper template engine (e.g. `envsubst`, `mustache`, or a small Python/Node script).

#### ARCH-03: CI commits directly to `main`

The GitHub Actions workflow commits the regenerated `docs/` back to `main`:

```yaml
git push
```

This bypasses branch protection rules if they are enabled and pollutes the commit history. The recommended approach is to deploy to a separate `gh-pages` branch using `actions/deploy-pages` with artifact upload, which requires no `contents: write` permission on `main`.

#### ARCH-04: JetBrains MCP install is a no-op

The `--ide jetbrains` branch in `install.sh` only `echo`s manual instructions. It writes no files. For skills and agent profiles, JetBrains falls through to the same `cp -R` as VSCode (since those are not IDE-specific), but for MCPs there is zero automation.

#### ARCH-05: GitLab CI is absent

`README.md` states the repository is "Git-platform agnostic and designed to work on GitHub and GitLab without changing core files." No `.gitlab-ci.yml` exists. GitLab Pages deployment requires a separate pipeline configuration with a different artifact upload and pages job structure.

---

## 5. Task Backlog

Tasks are grouped by theme and ordered by priority within each group. Each task includes a suggested acceptance criterion.

---

### Theme A — Global Install

#### TASK-A01: Add `--global` flag to `install.sh` for VSCode

**Priority:** P0
**Effort:** M

Extend `install.sh` to detect the VSCode user-level MCP config path per OS and merge the MCP server entry there when `--global` is passed.

*Acceptance criterion:* Running `./scripts/install.sh mcp atlassian --global --ide vscode` writes the `atlassian` server entry into the user-level `mcp.json` on Linux, macOS, and Windows (Git Bash) without overwriting existing entries.

---

#### TASK-A02: Add `--global` flag to `install.sh` for JetBrains

**Priority:** P0
**Effort:** M

Detect the JetBrains per-IDE config directory per OS and write the MCP server config when `--global --ide jetbrains` is passed. Handle multiple installed JetBrains IDEs.

*Acceptance criterion:* Running `./scripts/install.sh mcp atlassian --global --ide jetbrains` writes the config to the correct per-IDE directory on Linux and macOS, and prints the path for Windows (where the path is ambiguous).

---

#### TASK-A03: Define and implement global install path for skills and agent profiles

**Priority:** P1
**Effort:** S

Agree on a convention for user-level skill and agent profile storage (e.g. `~/.ai-catalog/skills/<name>/` and `~/.ai-catalog/agents/<name>/`). Implement this in `install.sh` for the `--global` flag on `skill` and `agent` types.

*Acceptance criterion:* `./scripts/install.sh skill jira-ticket-from-code --global` installs the skill to the agreed user-level path.

---

### Theme B — Marketplace One-Click Install

#### TASK-B01: Add copy-to-clipboard buttons to install code blocks

**Priority:** P1
**Effort:** S

Add a small copy icon button to each `<code class="oneliner">` block in the generated HTML. Pure JavaScript, no external dependencies.

*Acceptance criterion:* Clicking the button copies the install command to the clipboard and shows a brief "Copied!" confirmation.

---

#### TASK-B02: Implement `vscode://` deep-link handler for MCP installs

**Priority:** P2
**Effort:** L

VSCode supports `vscode://` URI extensions. Evaluate building a companion VS Code extension that registers a URI handler (`vscode://ai-catalog/install?type=mcp&name=atlassian`) so the marketplace page can trigger installs directly in the IDE.

*Acceptance criterion:* Clicking "Install in VSCode" on the marketplace page opens VS Code and installs the MCP server config into the user-level `mcp.json`.

---

#### TASK-B03: Add one-click install buttons to `generate-site.sh`

**Priority:** P1
**Effort:** S

Update the card template in `generate-site.sh` to include a copy button (TASK-B01) and optionally a `vscode://` link (TASK-B02) alongside the existing `<code>` block.

*Acceptance criterion:* Each card on the live marketplace shows a functional copy button.

---

### Theme C — CI Validation

#### TASK-C01: Create PR validation workflow

**Priority:** P0
**Effort:** S

Add `.github/workflows/validate-catalog.yml` that triggers on `pull_request` to `main`. It should run `generate-catalog.sh` and then run the validation script from TASK-C02.

*Acceptance criterion:* A PR that introduces a `SKILL.md` with missing `name` or `version` fields causes the check to fail and block merge.

---

#### TASK-C02: Write `scripts/validate-catalog.sh`

**Priority:** P0
**Effort:** M

Validate `catalog.json` after generation:

- Every item has non-empty `name`, `description`, and `path`
- Every `path` value resolves to an existing file or directory in the repo
- Every `SKILL.md` has `name`, `description`, and `version` in frontmatter
- Every `vscode.mcp.json` is valid JSON and contains a top-level `servers` object
- Every `AGENTS.md` is non-empty and does not start with a raw list item as its first body line

Exit non-zero on any failure, printing a clear message identifying the offending file.

*Acceptance criterion:* Script catches all listed failure cases in isolation tests.

---

#### TASK-C03: Fix CI to deploy via `gh-pages` branch instead of committing to `main`

**Priority:** P2
**Effort:** S

Replace the `git commit && git push` step in `deploy-pages.yml` with `actions/upload-pages-artifact` + `actions/deploy-pages`. Remove `contents: write` from the workflow permissions.

*Acceptance criterion:* Marketplace page updates on push to `main` without any commit appearing in the `main` branch history.

---

### Theme D — Data Quality

#### TASK-D01: Add YAML frontmatter to `AGENTS.md` files

**Priority:** P1
**Effort:** S

Add a frontmatter block to all `agents/<name>/AGENTS.md` files with at minimum `name` and `description` fields, matching the pattern used in `SKILL.md`.

*Acceptance criterion:* `agents/default/AGENTS.md` has a frontmatter block with a human-readable `description` field.

---

#### TASK-D02: Fix agent description extraction in `generate-catalog.sh`

**Priority:** P1
**Effort:** S

Update the agent discovery loop in `generate-catalog.sh` to parse `description` from the YAML frontmatter block (same logic as the skills loop) instead of using `awk` on the file body.

*Acceptance criterion:* The `default` agent card on the marketplace shows a proper description instead of `- Follow the existing code style and project conventions.`

---

#### TASK-D03: HTML-escape dynamic content in `generate-site.sh`

**Priority:** P2
**Effort:** M

Replace raw shell string interpolation for `name`, `description`, and `path` values with a helper that escapes `&`, `<`, `>`, and `"` before embedding in HTML attributes and text nodes.

*Acceptance criterion:* A description containing `<script>alert(1)</script>` renders as escaped text in the browser, not as executable HTML.

---

### Theme E — Templates

#### TASK-E01: Define templates catalog type and directory structure

**Priority:** P1
**Effort:** S

Create `templates/` directory with a `README.md` convention. Define required files for a template item (e.g. a `TEMPLATE.md` with frontmatter for `name`, `description`, `version`, and `type`).

*Acceptance criterion:* A sample template exists at `templates/default-pr-description/TEMPLATE.md` following the convention.

---

#### TASK-E02: Add template discovery to `generate-catalog.sh`

**Priority:** P1
**Effort:** S

Add a `templates_json` loop to `generate-catalog.sh` that discovers `templates/<name>/TEMPLATE.md` files, parses frontmatter, and includes them in `catalog.json` under a `templates` key.

*Acceptance criterion:* After adding a valid template, running `generate-catalog.sh` includes it in `catalog.json`.

---

#### TASK-E03: Add template install to `install.sh`

**Priority:** P1
**Effort:** S

Add a `template` case to `install.sh` that copies the template directory to `$PROJECT_PATH/.templates/<name>/` (project-level) or `~/.ai-catalog/templates/<name>/` (global).

*Acceptance criterion:* `./scripts/install.sh template default-pr-description --project /tmp/test` copies the template to `/tmp/test/.templates/default-pr-description/`.

---

#### TASK-E04: Add Templates section to `generate-site.sh`

**Priority:** P1
**Effort:** S

Add a templates card loop and a `<section id="templates">` to the generated HTML, with a matching nav tab.

*Acceptance criterion:* Marketplace page shows a Templates section when `catalog.json` contains template entries.

---

### Theme F — GitLab Support

#### TASK-F01: Add `.gitlab-ci.yml` for GitLab Pages deployment

**Priority:** P2
**Effort:** M

Create `.gitlab-ci.yml` with stages to run `generate-catalog.sh`, `generate-site.sh`, and deploy `docs/` to GitLab Pages. Add a `validate` stage (using TASK-C02) that runs on merge requests.

*Acceptance criterion:* Pushing to `main` on a GitLab mirror deploys the marketplace to GitLab Pages. An MR with an invalid catalog item fails the validate stage.

---

### Theme G — JetBrains

#### TASK-G01: Implement JetBrains MCP config file write in `install.sh`

**Priority:** P1
**Effort:** M

Replace the `echo`-only JetBrains branch with logic that detects the IDE config directory per OS and writes (or merges) the MCP server entry into the appropriate JSON config file.

*Acceptance criterion:* `./scripts/install.sh mcp atlassian --ide jetbrains` writes the server config to the correct directory on Linux and macOS without user interaction.

---

## 6. Prioritised Delivery Order

| Wave | Tasks | Goal |
|---|---|---|
| Wave 1 | C01, C02, D01, D02 | Stop broken content from shipping; fix existing data quality |
| Wave 2 | A01, A02, A03, B01, B03 | Deliver global install and copy-to-clipboard on the marketplace |
| Wave 3 | E01, E02, E03, E04, G01 | Templates support and JetBrains automation |
| Wave 4 | C03, D03, B02, F01 | CI hygiene, XSS hardening, deep-link install, GitLab |

---

## 7. Out of Scope

The following are noted for awareness but not tracked as tasks:

- Search or filtering on the marketplace page
- Authentication or access control for private catalog items
- Versioning or rollback of installed items
- A registry API to replace the static `catalog.json`
