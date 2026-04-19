#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CATALOG="$ROOT_DIR/catalog.json"
ERRORS=0

fail() {
  echo "ERROR: $1" >&2
  ERRORS=$((ERRORS + 1))
}

# catalog.json must exist and be valid JSON
if [ ! -f "$CATALOG" ]; then
  echo "ERROR: catalog.json not found at $CATALOG" >&2
  exit 1
fi

if ! jq empty "$CATALOG" 2>/dev/null; then
  echo "ERROR: catalog.json is not valid JSON" >&2
  exit 1
fi

parse_frontmatter_field() {
  local file="$1" field="$2"
  awk -v field="$field" '
    BEGIN {inside=0; c=0}
    /^---[[:space:]]*$/ {c++; if (c==1) {inside=1; next} if (c==2) {exit}}
    inside && $0 ~ "^[[:space:]]*" field ":" {
      sub("^[[:space:]]*" field ":[[:space:]]*", "")
      gsub(/"/, "")
      print; exit
    }
  ' "$file"
}

# Validate MCP items
while IFS= read -r item; do
  name="$(jq -r '.name' <<<"$item")"
  description="$(jq -r '.description' <<<"$item")"
  path="$(jq -r '.path' <<<"$item")"

  [ -z "$name" ]        && fail "MCP item has empty name: $item"
  [ -z "$description" ] && fail "MCP '$name': empty description"
  [ -z "$path" ]        && fail "MCP '$name': empty path"

  full_path="$ROOT_DIR/$path"
  [ ! -e "$full_path" ] && fail "MCP '$name': path does not exist: $path"

  vscode_mcp="$ROOT_DIR/$path/vscode.mcp.json"
  if [ -f "$vscode_mcp" ]; then
    if ! jq empty "$vscode_mcp" 2>/dev/null; then
      fail "MCP '$name': vscode.mcp.json is not valid JSON"
    elif ! jq -e '.servers' "$vscode_mcp" >/dev/null 2>&1; then
      fail "MCP '$name': vscode.mcp.json missing top-level 'servers' key"
    fi
  fi
done < <(jq -c '.mcp[]' "$CATALOG" 2>/dev/null || true)

# Validate skill items
while IFS= read -r item; do
  name="$(jq -r '.name' <<<"$item")"
  description="$(jq -r '.description' <<<"$item")"
  path="$(jq -r '.path' <<<"$item")"

  [ -z "$name" ]        && fail "Skill item has empty name: $item"
  [ -z "$description" ] && fail "Skill '$name': empty description"
  [ -z "$path" ]        && fail "Skill '$name': empty path"

  full_path="$ROOT_DIR/$path"
  [ ! -f "$full_path" ] && fail "Skill '$name': SKILL.md does not exist: $path"

  if [ -f "$full_path" ]; then
    fm_name="$(parse_frontmatter_field "$full_path" name)"
    fm_desc="$(parse_frontmatter_field "$full_path" description)"
    fm_ver="$(parse_frontmatter_field "$full_path" version)"
    [ -z "$fm_name" ]  && fail "Skill '$name': SKILL.md missing 'name' in frontmatter"
    [ -z "$fm_desc" ]  && fail "Skill '$name': SKILL.md missing 'description' in frontmatter"
    [ -z "$fm_ver" ]   && fail "Skill '$name': SKILL.md missing 'version' in frontmatter"
  fi
done < <(jq -c '.skills[]' "$CATALOG" 2>/dev/null || true)

# Validate agent items
while IFS= read -r item; do
  name="$(jq -r '.name' <<<"$item")"
  description="$(jq -r '.description' <<<"$item")"
  path="$(jq -r '.path' <<<"$item")"

  [ -z "$name" ]        && fail "Agent item has empty name: $item"
  [ -z "$description" ] && fail "Agent '$name': empty description"
  [ -z "$path" ]        && fail "Agent '$name': empty path"

  full_path="$ROOT_DIR/$path"
  [ ! -f "$full_path" ] && fail "Agent '$name': AGENTS.md does not exist: $path"

  if [ -f "$full_path" ]; then
    [ ! -s "$full_path" ] && fail "Agent '$name': AGENTS.md is empty"
    if [[ "$description" == -* ]]; then
      fail "Agent '$name': description starts with a bullet point — add YAML frontmatter with a prose description"
    fi
  fi
done < <(jq -c '.agents[]' "$CATALOG" 2>/dev/null || true)

# Validate template items (if present)
while IFS= read -r item; do
  name="$(jq -r '.name' <<<"$item")"
  description="$(jq -r '.description' <<<"$item")"
  path="$(jq -r '.path' <<<"$item")"

  [ -z "$name" ]        && fail "Template item has empty name: $item"
  [ -z "$description" ] && fail "Template '$name': empty description"
  [ -z "$path" ]        && fail "Template '$name': empty path"

  full_path="$ROOT_DIR/$path"
  [ ! -f "$full_path" ] && fail "Template '$name': TEMPLATE.md does not exist: $path"

  if [ -f "$full_path" ]; then
    fm_name="$(parse_frontmatter_field "$full_path" name)"
    fm_desc="$(parse_frontmatter_field "$full_path" description)"
    fm_ver="$(parse_frontmatter_field "$full_path" version)"
    [ -z "$fm_name" ]  && fail "Template '$name': TEMPLATE.md missing 'name' in frontmatter"
    [ -z "$fm_desc" ]  && fail "Template '$name': TEMPLATE.md missing 'description' in frontmatter"
    [ -z "$fm_ver" ]   && fail "Template '$name': TEMPLATE.md missing 'version' in frontmatter"
  fi
done < <(jq -c '.templates[]' "$CATALOG" 2>/dev/null || true)

if [ "$ERRORS" -gt 0 ]; then
  echo "Validation failed with $ERRORS error(s)." >&2
  exit 1
fi

echo "catalog.json validation passed."
