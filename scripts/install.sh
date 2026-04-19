#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./scripts/install.sh <mcp|skill|agent|template> <name> [options]

Options:
  --ide vscode|jetbrains   Target IDE (default: vscode; applies to mcp type)
  --project <path>         Install into this project directory (default: current directory)
  --global                 Install into user-level config instead of a project

Global install paths:
  VSCode MCP:     ~/Library/Application Support/Code/User/mcp.json  (macOS)
                  ~/.config/Code/User/mcp.json                       (Linux)
  JetBrains MCP:  ~/Library/Application Support/JetBrains/<IDE>/    (macOS)
                  ~/.config/JetBrains/<IDE>/                         (Linux)
  Skills/Agents:  ~/.ai-catalog/skills/<name>/
                  ~/.ai-catalog/agents/<name>/
  Templates:      ~/.ai-catalog/templates/<name>/
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
GLOBAL=false

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
    --global)
      GLOBAL=true
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

detect_os() {
  case "$(uname -s)" in
    Darwin)               echo "mac" ;;
    Linux)                echo "linux" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *)                    echo "unknown" ;;
  esac
}

vscode_global_mcp_path() {
  local os
  os="$(detect_os)"
  case "$os" in
    mac)     echo "$HOME/Library/Application Support/Code/User/mcp.json" ;;
    linux)   echo "${XDG_CONFIG_HOME:-$HOME/.config}/Code/User/mcp.json" ;;
    windows) echo "${APPDATA}/Code/User/mcp.json" ;;
    *)       echo "$HOME/.config/Code/User/mcp.json" ;;
  esac
}

jetbrains_config_root() {
  local os
  os="$(detect_os)"
  case "$os" in
    mac)     echo "$HOME/Library/Application Support/JetBrains" ;;
    linux)   echo "${XDG_CONFIG_HOME:-$HOME/.config}/JetBrains" ;;
    windows) echo "${APPDATA}/JetBrains" ;;
    *)       echo "$HOME/.config/JetBrains" ;;
  esac
}

merge_mcp_json() {
  local source="$1" target="$2"
  local target_dir
  target_dir="$(dirname "$target")"
  mkdir -p "$target_dir"
  if [ -f "$target" ]; then
    local tmp_file
    tmp_file="$(mktemp)"
    jq -s '{servers: ((.[0].servers // {}) + (.[1].servers // {}))}' "$target" "$source" > "$tmp_file"
    mv "$tmp_file" "$target"
  else
    cp "$source" "$target"
  fi
}

case "$TYPE" in
  mcp)
    SOURCE="$ROOT_DIR/mcp/$NAME/vscode.mcp.json"
    README_PATH="$ROOT_DIR/mcp/$NAME/README.md"

    if [ ! -f "$README_PATH" ]; then
      echo "MCP '$NAME' not found at mcp/$NAME"
      exit 1
    fi

    if [ ! -f "$SOURCE" ]; then
      echo "No vscode.mcp.json found for MCP '$NAME'"
      exit 1
    fi

    if [ "$IDE" = "vscode" ]; then
      if $GLOBAL; then
        TARGET="$(vscode_global_mcp_path)"
        merge_mcp_json "$SOURCE" "$TARGET"
        echo "Installed MCP '$NAME' into global VSCode config: $TARGET"
      else
        mkdir -p "$PROJECT_PATH/.vscode"
        TARGET="$PROJECT_PATH/.vscode/mcp.json"
        merge_mcp_json "$SOURCE" "$TARGET"
        echo "Installed MCP '$NAME' config into $TARGET"
      fi

    elif [ "$IDE" = "jetbrains" ]; then
      JB_ROOT="$(jetbrains_config_root)"

      if [ "$(detect_os)" = "windows" ]; then
        echo "JetBrains MCP setup on Windows:"
        echo "  Config root: $JB_ROOT"
        echo "  Open Settings > Tools > AI Assistant > MCP and add a stdio server."
        echo "  See $README_PATH for details."
        exit 0
      fi

      if [ ! -d "$JB_ROOT" ]; then
        echo "JetBrains config directory not found at $JB_ROOT"
        echo "Manual setup: Settings > Tools > AI Assistant > MCP"
        echo "See $README_PATH for details."
        exit 0
      fi

      installed_count=0
      while IFS= read -r ide_dir; do
        TARGET="$ide_dir/mcp.json"
        merge_mcp_json "$SOURCE" "$TARGET"
        echo "Installed MCP '$NAME' into $TARGET"
        installed_count=$((installed_count + 1))
      done < <(find "$JB_ROOT" -mindepth 1 -maxdepth 1 -type d \
        \( -name 'IntelliJIdea*' -o -name 'WebStorm*' -o -name 'PyCharm*' \
           -o -name 'GoLand*' -o -name 'CLion*' -o -name 'Rider*' \
           -o -name 'DataGrip*' -o -name 'RubyMine*' -o -name 'PhpStorm*' \) \
        2>/dev/null | sort)

      if [ "$installed_count" -eq 0 ]; then
        echo "No JetBrains IDE directories found under $JB_ROOT"
        echo "Manual setup: Settings > Tools > AI Assistant > MCP"
        echo "See $README_PATH for details."
      fi

    else
      echo "Unsupported IDE: $IDE"
      exit 1
    fi
    ;;

  skill)
    SOURCE_DIR="$ROOT_DIR/skills/$NAME"

    if [ ! -d "$SOURCE_DIR" ]; then
      echo "Skill '$NAME' not found at skills/$NAME"
      exit 1
    fi

    if $GLOBAL; then
      TARGET_DIR="$HOME/.ai-catalog/skills/$NAME"
    else
      TARGET_DIR="$PROJECT_PATH/.skills/$NAME"
      mkdir -p "$PROJECT_PATH/.skills"
    fi

    mkdir -p "$(dirname "$TARGET_DIR")"
    rm -rf "$TARGET_DIR"
    cp -R "$SOURCE_DIR" "$TARGET_DIR"
    echo "Installed skill '$NAME' into $TARGET_DIR"
    ;;

  agent)
    SOURCE_DIR="$ROOT_DIR/agents/$NAME"

    if [ ! -d "$SOURCE_DIR" ]; then
      echo "Agent profile '$NAME' not found at agents/$NAME"
      exit 1
    fi

    if $GLOBAL; then
      TARGET_DIR="$HOME/.ai-catalog/agents/$NAME"
    else
      TARGET_DIR="$PROJECT_PATH/.agents/$NAME"
      mkdir -p "$PROJECT_PATH/.agents"
    fi

    mkdir -p "$(dirname "$TARGET_DIR")"
    rm -rf "$TARGET_DIR"
    cp -R "$SOURCE_DIR" "$TARGET_DIR"
    echo "Installed agent profile '$NAME' into $TARGET_DIR"
    ;;

  template)
    SOURCE_DIR="$ROOT_DIR/templates/$NAME"

    if [ ! -d "$SOURCE_DIR" ]; then
      echo "Template '$NAME' not found at templates/$NAME"
      exit 1
    fi

    if $GLOBAL; then
      TARGET_DIR="$HOME/.ai-catalog/templates/$NAME"
    else
      TARGET_DIR="$PROJECT_PATH/.templates/$NAME"
      mkdir -p "$PROJECT_PATH/.templates"
    fi

    mkdir -p "$(dirname "$TARGET_DIR")"
    rm -rf "$TARGET_DIR"
    cp -R "$SOURCE_DIR" "$TARGET_DIR"
    echo "Installed template '$NAME' into $TARGET_DIR"
    ;;

  *)
    echo "Unsupported type: $TYPE"
    usage
    exit 1
    ;;
esac
