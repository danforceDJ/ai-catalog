#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
command -v uv >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/" >&2; exit 1; }
uv run --script "$REPO_ROOT/system/scripts/generate_catalog.py"
uv run --script "$REPO_ROOT/system/scripts/generate_marketplace.py"
git -C "$REPO_ROOT" add system/artifacts/catalog.json .github/plugin/marketplace.json
