# CI/CD Pipeline

---

## GitHub Actions

### `validate-catalog.yml` — runs on every PR to `main`/`master`

| Step | Command | Fails if |
|---|---|---|
| Validate catalog | `uv run --script scripts/validate_catalog.py` | Any validation error |
| Run test suite | `uv run --with pytest --with pyyaml --with jsonschema --with jinja2 -- pytest -q` | Any test failure |
| Freshness check `catalog.json` | Regenerates + compares (ignoring `generated_at`) | Content mismatch — must commit updated `catalog.json` in the PR |
| Freshness check `marketplace.json` | Regenerates + `git diff --exit-code` | Content mismatch — must commit updated `.github/plugin/marketplace.json` in the PR |

### `deploy-site.yml` — runs on push to `main`/`master` + `workflow_dispatch`

| Step | Command |
|---|---|
| Generate zips | `uv run --script scripts/generate_zips.py` |
| Generate site | `uv run --script scripts/generate_site.py` |
| Upload artifact | `actions/upload-pages-artifact@v3` (uploads `docs/`) |
| Deploy | `actions/deploy-pages@v4` |

Reads the committed `catalog.json` — does **not** re-run `generate_catalog.py`.

Required job permissions: `pages: write`, `id-token: write`

---

## GitLab CI (`.gitlab-ci.yml`)

Two stages using `alpine:latest` + `uv` (fetched at runtime):

| Stage | Trigger | Script |
|---|---|---|
| `validate` | Merge requests | `generate-catalog.sh` + `validate-catalog.sh` |
| `pages` | Default branch push | `generate-catalog.sh` + `generate-site.sh` → `mv docs public` |

Artifact: `public/` for GitLab Pages.

---

## Pre-commit Hooks (`.pre-commit-config.yaml`)

Install: `uv tool install pre-commit && pre-commit install`

| Hook | Triggered by file pattern | Action |
|---|---|---|
| `regenerate-catalog` | `^(plugins/.*\|templates/.*\|marketplace\.config\.json$)` | Runs `generate_catalog.py` + `generate_marketplace.py`, then `git add catalog.json .github/plugin/marketplace.json` |
| `validate-catalog` | plugins, templates, config, or tracked artifacts | Runs `validate_catalog.py` |

> **Caveat:** Hooks run against the full working tree, not only staged files. If you use `git add -p`, regenerate artefacts manually before committing.

---

## PR Checklist (manual steps required)

When adding or modifying any plugin, primitive, or template:

```bash
# 1. Validate
uv run --script scripts/validate_catalog.py

# 2. Regenerate tracked artefacts
uv run --script scripts/generate_catalog.py
uv run --script scripts/generate_marketplace.py

# 3. Commit everything together
git add catalog.json .github/plugin/marketplace.json plugins/ skills/ agents/ commands/ mcpServers/ templates/
git commit -m "feat: ..."
```

CI will fail the freshness check if `catalog.json` or `marketplace.json` are stale.

