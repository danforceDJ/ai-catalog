# Design: Codebase Cleanup & Onboarding Improvement

**Date:** 2026-04-21  
**Status:** Approved  
**Scope:** Remove redundant scripts/files, eliminate duplicated bash/Python logic, automate catalog regeneration via pre-commit hook

---

## Problem Statement

The repo has three sources of friction:

1. **Duplicated logic** — three bash scripts (`generate-catalog.sh`, `generate-site.sh`, `validate-catalog.sh`) each duplicate the logic of their Python counterparts, creating ~850 lines of dead maintenance weight. GitLab CI requires the bash entry points, but not the duplicated logic.

2. **Manual regeneration step** — adding or modifying a plugin requires remembering to run two generator scripts and commit their outputs separately. Missing this step causes CI freshness checks to fail.

3. **Scattered documentation** — `Analysis.md` (15KB gap analysis) lives at the root but is not referenced anywhere; useful insights are effectively lost. `scripts/schemas/` contains JSON schema files loaded by nothing.

---

## Design

### 1. Bash Scripts → Thin Wrappers

**What changes:** `scripts/generate-catalog.sh`, `scripts/generate-site.sh`, and `scripts/validate-catalog.sh` are replaced with thin delegators (~5 lines each) that verify `uv` is available and then invoke the equivalent Python script.

**Example (`generate-catalog.sh` after):**
```bash
#!/usr/bin/env bash
set -euo pipefail
command -v uv >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
uv run --script "$(dirname "$0")/generate_catalog.py" "$@"
```

**What stays the same:** `.gitlab-ci.yml` continues calling the same script names — no GitLab config changes required. `install.sh` is untouched (deprecated banner already in place, still functional as a fallback).

**Result:** ~850 lines of duplicated logic removed. Future generator changes only need to happen once, in Python.

---

### 2. Pre-commit Hook via `.pre-commit-config.yaml`

**What changes:** A `.pre-commit-config.yaml` is added at the repo root, defining two local hooks:

| Hook | Trigger | Command | Auto-stages |
|------|---------|---------|-------------|
| `regenerate-catalog` | Changes to `plugins/**`, `templates/**`, `marketplace.config.json` | `generate_catalog.py` + `generate_marketplace.py` | `catalog.json`, `.github/plugin/marketplace.json` |
| `validate-catalog` | Always (runs after regenerate) | `validate_catalog.py` | — (blocks commit on failure) |

Hook order is fixed: regenerate runs before validate, so validation always sees fresh outputs.

`generate_site.py` and `generate_zips.py` are **excluded** from the hook — their outputs (HTML, zips) belong in the deploy pipeline, not in every commit.

**Setup (one-time per contributor):**
```bash
uv run --with pre-commit pre-commit install
```

No global install required. `uv` handles `pre-commit` ephemerally. This command is documented in `CONTRIBUTING.md`.

**Result:** Contributors can no longer accidentally commit stale `catalog.json` or `marketplace.json`. The validator runs automatically and blocks commits with clear error output.

---

### 3. Documentation Consolidation

**`Analysis.md`:** Useful design invariants and onboarding guidance are merged into `CONTRIBUTING.md` under the existing "Adding New Catalog Items" section. Gap observations that are now resolved are discarded. `Analysis.md` is deleted after the merge.

**`CONTRIBUTING.md` additions:**
- "Local development setup" section: one-time `pre-commit install` command, explanation of what it does
- Manual generator commands for contributors who want to run them outside of a commit
- Clarification that `catalog.json` and `.github/plugin/marketplace.json` are auto-staged by the hook

**`.idea/` directory:** Added to `.gitignore`. Existing local JetBrains config is unaffected; it stops appearing in `git status` for all contributors.

**`scripts/schemas/`:** Deleted. The JSON schema files are not imported or referenced anywhere in the codebase. If schema validation is added in the future, `validate_catalog.py` is the correct location.

---

## Architecture: What Changes vs. What Stays

```
BEFORE:
plugins/ + templates/ → [manual: uv run generate_catalog.py]
                       → [manual: uv run generate_marketplace.py]
                       → [manual: git add + commit outputs]
                       → CI freshness check (fails if forgotten)

AFTER:
plugins/ + templates/ → git commit
                       → pre-commit: regenerate hook fires automatically
                       → pre-commit: validate hook fires
                       → outputs auto-staged → commit succeeds
                       → CI freshness check (always passes)
```

GitLab CI path is unchanged in behavior — bash wrappers delegate to Python, same outputs.

---

## Files Changed

| Action | Path |
|--------|------|
| Replace (thin wrapper) | `scripts/generate-catalog.sh` |
| Replace (thin wrapper) | `scripts/generate-site.sh` |
| Replace (thin wrapper) | `scripts/validate-catalog.sh` |
| Add | `.pre-commit-config.yaml` |
| Update | `CONTRIBUTING.md` (merge Analysis.md content + pre-commit setup docs) |
| Delete | `Analysis.md` |
| Delete | `scripts/schemas/` (entire directory) |
| Update | `.gitignore` (add `.idea/`) |

**Not changed:** `.gitlab-ci.yml`, `install.sh`, all Python scripts, all plugins, all templates, all GitHub Actions workflows.

---

## Testing

- After replacing bash wrappers: verify GitLab pipeline passes (push to a branch and check pipeline output)
- After adding pre-commit config: run `pre-commit run --all-files` and confirm both hooks pass on a clean repo
- Verify that modifying a plugin file and committing auto-stages updated `catalog.json` and `marketplace.json`
- Verify that introducing a validation error (e.g., duplicate plugin name) blocks the commit with a clear message

---

## Non-Goals

- Scaffolding script for new plugins (not in scope — pre-commit hook addresses the commit-time friction)
- Migrating GitLab CI to Python-native tooling (out of scope — bash wrappers are sufficient)
- Changing the deploy pipeline or GitHub Actions workflows
