#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./scripts/install.sh <mcp|skill|agent> <name> [--ide vscode|jetbrains] [--project <path>]
USAGE
}

if [ "$#" -lt 2 ]; then
  usage
  exit 1
fi

TYPE="$1"
NAME="$2"
shift 2

IDE="vscode"
PROJECT_PATH="$(pwd)"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --ide)
      IDE="${2:-}"
      shift 2
      ;;
    --project)
      PROJECT_PATH="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

case "$TYPE" in
  mcp)
    SOURCE="$ROOT_DIR/mcp/$NAME/vscode.mcp.json"
    README_PATH="$ROOT_DIR/mcp/$NAME/README.md"

    if [ ! -f "$README_PATH" ]; then
      echo "MCP '$NAME' not found at mcp/$NAME"
      exit 1
    fi

    if [ "$IDE" = "vscode" ]; then
      if [ ! -f "$SOURCE" ]; then
        echo "No vscode.mcp.json found for MCP '$NAME'"
        exit 1
      fi

      mkdir -p "$PROJECT_PATH/.vscode"
      TARGET="$PROJECT_PATH/.vscode/mcp.json"

      if [ -f "$TARGET" ]; then
        tmp_file="$(mktemp)"
        jq -s '{servers: ((.[0].servers // {}) + (.[1].servers // {}))}' "$TARGET" "$SOURCE" > "$tmp_file"
        mv "$tmp_file" "$TARGET"
      else
        cp "$SOURCE" "$TARGET"
      fi

      echo "Installed MCP '$NAME' config into $TARGET"
    elif [ "$IDE" = "jetbrains" ]; then
      echo "JetBrains MCP setup is manual for '$NAME'."
      echo "See: $README_PATH"
      echo
      echo "In IntelliJ: Settings -> Tools -> AI Assistant -> MCP"
      echo "Add stdio server with command: npx"
      echo "Args: -y mcp-remote@latest https://mcp.atlassian.com/v1/sse"
    else
      echo "Unsupported IDE: $IDE"
      exit 1
    fi
    ;;

  skill)
    SOURCE_DIR="$ROOT_DIR/skills/$NAME"
    TARGET_DIR="$PROJECT_PATH/.skills/$NAME"

    if [ ! -d "$SOURCE_DIR" ]; then
      echo "Skill '$NAME' not found at skills/$NAME"
      exit 1
    fi

    mkdir -p "$PROJECT_PATH/.skills"
    rm -rf "$TARGET_DIR"
    cp -R "$SOURCE_DIR" "$TARGET_DIR"
    echo "Installed skill '$NAME' into $TARGET_DIR"
    ;;

  agent)
    SOURCE_DIR="$ROOT_DIR/agents/$NAME"
    TARGET_DIR="$PROJECT_PATH/.agents/$NAME"

    if [ ! -d "$SOURCE_DIR" ]; then
      echo "Agent profile '$NAME' not found at agents/$NAME"
      exit 1
    fi

    mkdir -p "$PROJECT_PATH/.agents"
    rm -rf "$TARGET_DIR"
    cp -R "$SOURCE_DIR" "$TARGET_DIR"
    echo "Installed agent profile '$NAME' into $TARGET_DIR"
    ;;

  *)
    echo "Unsupported type: $TYPE"
    usage
    exit 1
    ;;
esac
