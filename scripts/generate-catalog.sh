#!/usr/bin/env bash
set -euo pipefail
command -v uv >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
uv run --script "$(dirname "$0")/generate_catalog.py" "$@"
