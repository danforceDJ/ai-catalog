#!/usr/bin/env bash
set -euo pipefail
command -v uv >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/" >&2; exit 1; }
uv run --script "$(dirname "$0")/validate_catalog.py" "$@"
