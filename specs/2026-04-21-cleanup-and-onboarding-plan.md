# Codebase Cleanup & Onboarding Improvement — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace ~850 lines of duplicate bash logic with thin wrappers, add a pre-commit hook that auto-regenerates catalog outputs on every commit, and consolidate scattered documentation.

**Architecture:** Three existing bash scripts become 5-line `uv`-delegating wrappers (GitLab CI calls the same filenames, so no pipeline changes needed). A new `scripts/hooks/` directory holds two hook scripts referenced from `.pre-commit-config.yaml`. `CONTRIBUTING.md` gains a local-dev-setup section; `Analysis.md` and `scripts/schemas/` are deleted.

**Tech Stack:** bash, `uv` (PEP 723), `pre-commit` (Python), pytest (existing test suite)

---

## File Map

| Action | Path |
|--------|------|
| Replace | `scripts/generate-catalog.sh` |
| Replace | `scripts/generate-site.sh` |
| Replace | `scripts/validate-catalog.sh` |
| Create | `scripts/hooks/regenerate-catalog.sh` |
| Create | `scripts/hooks/validate-catalog.sh` |
| Create | `.pre-commit-config.yaml` |
| Modify | `CONTRIBUTING.md` |
| Modify | `.gitignore` |
| Delete | `Analysis.md` |
| Delete | `scripts/schemas/` (directory) |

---

### Task 1: Replace bash scripts with thin wrappers

Each of the three bash scripts is replaced with a 5-line wrapper that delegates to its Python counterpart. GitLab CI calls the same filenames — no `.gitlab-ci.yml` changes required.

**Files:**
- Modify: `scripts/generate-catalog.sh`
- Modify: `scripts/generate-site.sh`
- Modify: `scripts/validate-catalog.sh`

- [ ] **Step 1: Verify current bash scripts produce correct output (baseline)**

Run from the repo root:
```bash
uv run --script scripts/generate_catalog.py
cp catalog.json /tmp/catalog-python.json
bash scripts/generate-catalog.sh
diff /tmp/catalog-python.json catalog.json
```
Expected: diff shows no differences (both scripts produce identical output). If they differ, note the difference before proceeding — the wrapper approach assumes Python is the source of truth.

- [ ] **Step 2: Replace `generate-catalog.sh` with thin wrapper**

Overwrite the entire file with:
```bash
#!/usr/bin/env bash
set -euo pipefail
command -v uv >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
uv run --script "$(dirname "$0")/generate_catalog.py" "$@"
```

- [ ] **Step 3: Replace `generate-site.sh` with thin wrapper**

Overwrite the entire file with:
```bash
#!/usr/bin/env bash
set -euo pipefail
command -v uv >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
uv run --script "$(dirname "$0")/generate_site.py" "$@"
```

- [ ] **Step 4: Replace `validate-catalog.sh` with thin wrapper**

Overwrite the entire file with:
```bash
#!/usr/bin/env bash
set -euo pipefail
command -v uv >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
uv run --script "$(dirname "$0")/validate_catalog.py" "$@"
```

- [ ] **Step 5: Make wrappers executable**

```bash
chmod +x scripts/generate-catalog.sh scripts/generate-site.sh scripts/validate-catalog.sh
```

- [ ] **Step 6: Verify wrappers work**

```bash
bash scripts/generate-catalog.sh
```
Expected: `Generated .../catalog.json` (same output as before, no errors)

```bash
bash scripts/validate-catalog.sh
```
Expected: `catalog.json validation passed.`

```bash
bash -n scripts/generate-catalog.sh && bash -n scripts/generate-site.sh && bash -n scripts/validate-catalog.sh
```
Expected: no output (syntax check passes)

- [ ] **Step 7: Run existing test suite to confirm nothing broken**

```bash
uv run --with pytest --with pyyaml --with jsonschema --with jinja2 -- pytest -q
```
Expected: all tests pass

- [ ] **Step 8: Commit**

```bash
git add scripts/generate-catalog.sh scripts/generate-site.sh scripts/validate-catalog.sh
git commit -m "refactor: replace bash scripts with thin uv-delegating wrappers"
```

---

### Task 2: Create hook scripts

Two small scripts in a new `scripts/hooks/` directory. These are the entry points for the pre-commit hooks added in Task 3.

**Files:**
- Create: `scripts/hooks/regenerate-catalog.sh`
- Create: `scripts/hooks/validate-catalog.sh`

- [ ] **Step 1: Create `scripts/hooks/` directory**

```bash
mkdir -p scripts/hooks
```

- [ ] **Step 2: Create `scripts/hooks/regenerate-catalog.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
command -v uv >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
uv run --script "$REPO_ROOT/scripts/generate_catalog.py"
uv run --script "$REPO_ROOT/scripts/generate_marketplace.py"
git -C "$REPO_ROOT" add catalog.json .github/plugin/marketplace.json
```

- [ ] **Step 3: Create `scripts/hooks/validate-catalog.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
command -v uv >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
uv run --script "$REPO_ROOT/scripts/validate_catalog.py"
```

- [ ] **Step 4: Make hook scripts executable**

```bash
chmod +x scripts/hooks/regenerate-catalog.sh scripts/hooks/validate-catalog.sh
```

- [ ] **Step 5: Verify hook scripts work standalone**

```bash
bash scripts/hooks/regenerate-catalog.sh
```
Expected: `Generated .../catalog.json` and `Generated .../marketplace.json`, then `catalog.json` and `.github/plugin/marketplace.json` are staged (verify with `git status`).

```bash
bash scripts/hooks/validate-catalog.sh
```
Expected: `catalog.json validation passed.`

- [ ] **Step 6: Commit**

```bash
git add scripts/hooks/
git commit -m "feat: add pre-commit hook scripts for catalog regeneration and validation"
```

---

### Task 3: Add `.pre-commit-config.yaml`

Defines two local hooks. `regenerate-catalog` fires when plugin/template files change and auto-stages the outputs. `validate-catalog` fires whenever catalog-related files are in the commit.

**Files:**
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: Create `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: local
    hooks:
      - id: regenerate-catalog
        name: Regenerate catalog + marketplace manifest
        entry: scripts/hooks/regenerate-catalog.sh
        language: script
        pass_filenames: false
        files: ^(plugins/|templates/|marketplace\.config\.json)

      - id: validate-catalog
        name: Validate catalog
        entry: scripts/hooks/validate-catalog.sh
        language: script
        pass_filenames: false
        files: ^(plugins/|templates/|marketplace\.config\.json|catalog\.json|\.github/plugin/marketplace\.json)
```

- [ ] **Step 2: Install pre-commit hooks locally**

```bash
uv run --with pre-commit pre-commit install
```
Expected output ends with: `pre-commit installed at .git/hooks/pre-commit`

- [ ] **Step 3: Run hooks against all files to verify they pass on the current repo**

```bash
uv run --with pre-commit pre-commit run --all-files
```
Expected: both hooks show `Passed` (or `Skipped` for regenerate-catalog if no plugin files are staged)

- [ ] **Step 4: Smoke-test the commit-time flow**

Make a trivial change to a plugin file, stage it, and commit:
```bash
# Add a blank line to any plugin.json and immediately remove it
echo "" >> plugins/atlassian-mcp/plugin.json
git add plugins/atlassian-mcp/plugin.json
git commit -m "test: trigger pre-commit hook"
```
Expected: the commit completes, `catalog.json` and `.github/plugin/marketplace.json` appear in the commit (auto-staged by the regenerate hook). Revert the test commit afterward:
```bash
git revert HEAD --no-edit
```

- [ ] **Step 5: Commit the config file**

```bash
git add .pre-commit-config.yaml
git commit -m "feat: add pre-commit hooks for catalog regeneration and validation"
```

---

### Task 4: Update `CONTRIBUTING.md`

Two changes: (1) the manual regeneration step is updated to mention it's now handled automatically, (2) a new "Local development setup" section is added at the top.

**Files:**
- Modify: `CONTRIBUTING.md`

- [ ] **Step 1: Add "Local development setup" section after the opening paragraph**

Insert this block immediately after the first line (`Thanks for contributing to the AI catalog.`):

```markdown
## Local development setup

Install the pre-commit hooks once per clone — they auto-regenerate `catalog.json` and `.github/plugin/marketplace.json` on every commit so you never have to remember to do it manually:

```bash
uv run --with pre-commit pre-commit install
```

To run generators manually (outside of a commit):
```bash
uv run --script scripts/generate_catalog.py
uv run --script scripts/generate_marketplace.py
```

To validate the catalog without committing:
```bash
uv run --script scripts/validate_catalog.py
```
```

- [ ] **Step 2: Update step 5 of "Adding a new plugin" to reflect automation**

Replace the current step 5:
```markdown
5. Regenerate tracked artefacts and commit them:
   ```bash
   uv run --script scripts/generate_catalog.py
   uv run --script scripts/generate_marketplace.py
   git add catalog.json .github/plugin/marketplace.json
   git commit -m "chore: regenerate catalog"
   ```
```

With:
```markdown
5. Stage your files and commit. If you installed the pre-commit hook (see **Local development setup** above), `catalog.json` and `.github/plugin/marketplace.json` are regenerated and staged automatically. If you skipped hook setup, regenerate manually first:
   ```bash
   uv run --script scripts/generate_catalog.py
   uv run --script scripts/generate_marketplace.py
   git add catalog.json .github/plugin/marketplace.json
   ```
```

- [ ] **Step 3: Verify the file looks right**

```bash
cat CONTRIBUTING.md
```
Confirm: "Local development setup" section appears near the top; step 5 mentions the hook and still includes the manual fallback commands.

- [ ] **Step 4: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add local dev setup section and update regen step for pre-commit hook"
```

---

### Task 5: Cleanup — delete stale files and update `.gitignore`

Remove `Analysis.md` (insights merged into CONTRIBUTING.md in Task 4), `scripts/schemas/` (two JSON schema files referenced by nothing), and add `.idea/` to `.gitignore`.

**Files:**
- Delete: `Analysis.md`
- Delete: `scripts/schemas/marketplace.schema.json`
- Delete: `scripts/schemas/plugin.schema.json`
- Modify: `.gitignore`

- [ ] **Step 1: Verify `scripts/schemas/` is unused**

```bash
grep -r "schemas/" scripts/ tests/ .github/ --include="*.py" --include="*.sh" --include="*.yml" --include="*.yaml"
```
Expected: no matches (confirms nothing imports or references these files).

- [ ] **Step 2: Delete stale files**

```bash
rm Analysis.md
rm -rf scripts/schemas/
```

- [ ] **Step 3: Add `.idea/` to `.gitignore`**

Open `.gitignore` and add `.idea/` on a new line in the appropriate section. The file currently looks like:
```
docs/superpowers/
.idea/
...
```
`.idea/` is already present. Confirm it's there:
```bash
grep -n '\.idea' .gitignore
```
Expected: one match. If it's already there, no edit needed. If it's missing, add it.

- [ ] **Step 4: Run the full test suite one final time**

```bash
uv run --with pytest --with pyyaml --with jsonschema --with jinja2 -- pytest -q
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add -u Analysis.md scripts/schemas/
git add .gitignore
git commit -m "chore: delete stale Analysis.md and unused schemas/, gitignore .idea/"
```

---

## Done criteria

- [ ] `scripts/generate-catalog.sh`, `generate-site.sh`, `validate-catalog.sh` are each ≤6 lines and delegate to Python
- [ ] `scripts/hooks/regenerate-catalog.sh` and `validate-catalog.sh` exist and are executable
- [ ] `.pre-commit-config.yaml` exists at repo root; `pre-commit run --all-files` passes
- [ ] Committing a change to a plugin file auto-stages updated `catalog.json` and `marketplace.json`
- [ ] `CONTRIBUTING.md` has a "Local development setup" section with `pre-commit install` command
- [ ] `Analysis.md` is deleted
- [ ] `scripts/schemas/` is deleted
- [ ] All pytest tests pass
