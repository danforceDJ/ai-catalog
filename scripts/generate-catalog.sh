#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mcp_json='[]'
if [ -d "$ROOT_DIR/mcp" ]; then
  while IFS= read -r -d '' dir; do
    name="$(basename "$dir")"
    readme="$dir/README.md"
    description=""
    if [ -f "$readme" ]; then
      description="$(awk 'NF && $0 !~ /^#/ {print; exit}' "$readme" | sed 's/"/\\"/g')"
    fi
    mcp_json="$(jq -c --arg name "$name" --arg description "$description" --arg path "mcp/$name" '. + [{name:$name,description:$description,path:$path}]' <<<"$mcp_json")"
  done < <(find "$ROOT_DIR/mcp" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
fi

skills_json='[]'
if [ -d "$ROOT_DIR/skills" ]; then
  while IFS= read -r -d '' skill_md; do
    dir="$(dirname "$skill_md")"
    default_name="$(basename "$dir")"

    frontmatter="$(awk '
      BEGIN {inside=0; c=0}
      /^---[[:space:]]*$/ {c++; if (c==1) {inside=1; next} if (c==2) {exit}}
      inside {print}
    ' "$skill_md")"

    name="$(awk -F': *' '/^name:/ {print $2; exit}' <<<"$frontmatter")"
    description="$(awk -F': *' '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}' <<<"$frontmatter")"
    version="$(awk '/^[[:space:]]*version:[[:space:]]*/ {sub(/^[[:space:]]*version:[[:space:]]*/, ""); gsub(/"/, ""); print; exit}' <<<"$frontmatter")"

    name="${name:-$default_name}"

    skills_json="$(jq -c --arg name "$name" --arg description "$description" --arg version "$version" --arg path "skills/$default_name/SKILL.md" '. + [{name:$name,description:$description,version:$version,path:$path}]' <<<"$skills_json")"
  done < <(find "$ROOT_DIR/skills" -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' -print0 | sort -z)
fi

agents_json='[]'
if [ -d "$ROOT_DIR/agents" ]; then
  while IFS= read -r -d '' agent_md; do
    dir="$(dirname "$agent_md")"
    default_name="$(basename "$dir")"

    frontmatter="$(awk '
      BEGIN {inside=0; c=0}
      /^---[[:space:]]*$/ {c++; if (c==1) {inside=1; next} if (c==2) {exit}}
      inside {print}
    ' "$agent_md")"

    name="$(awk -F': *' '/^name:/ {print $2; exit}' <<<"$frontmatter")"
    description="$(awk -F': *' '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}' <<<"$frontmatter")"
    name="${name:-$default_name}"

    agents_json="$(jq -c --arg name "$name" --arg description "$description" --arg path "agents/$default_name/AGENTS.md" '. + [{name:$name,description:$description,path:$path}]' <<<"$agents_json")"
  done < <(find "$ROOT_DIR/agents" -mindepth 2 -maxdepth 2 -type f -name 'AGENTS.md' -print0 | sort -z)
fi

templates_json='[]'
if [ -d "$ROOT_DIR/templates" ]; then
  while IFS= read -r -d '' template_md; do
    dir="$(dirname "$template_md")"
    default_name="$(basename "$dir")"

    frontmatter="$(awk '
      BEGIN {inside=0; c=0}
      /^---[[:space:]]*$/ {c++; if (c==1) {inside=1; next} if (c==2) {exit}}
      inside {print}
    ' "$template_md")"

    name="$(awk -F': *' '/^name:/ {print $2; exit}' <<<"$frontmatter")"
    description="$(awk -F': *' '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}' <<<"$frontmatter")"
    version="$(awk '/^[[:space:]]*version:[[:space:]]*/ {sub(/^[[:space:]]*version:[[:space:]]*/, ""); gsub(/"/, ""); print; exit}' <<<"$frontmatter")"
    type="$(awk -F': *' '/^type:/ {print $2; exit}' <<<"$frontmatter")"

    name="${name:-$default_name}"

    templates_json="$(jq -c --arg name "$name" --arg description "$description" --arg version "$version" --arg type "$type" --arg path "templates/$default_name/TEMPLATE.md" '. + [{name:$name,description:$description,version:$version,type:$type,path:$path}]' <<<"$templates_json")"
  done < <(find "$ROOT_DIR/templates" -mindepth 2 -maxdepth 2 -type f -name 'TEMPLATE.md' -print0 | sort -z)
fi

jq -n \
  --arg generated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson mcp "$mcp_json" \
  --argjson skills "$skills_json" \
  --argjson agents "$agents_json" \
  --argjson templates "$templates_json" \
  '{generated_at:$generated_at,mcp:$mcp,skills:$skills,agents:$agents,templates:$templates}' > "$ROOT_DIR/catalog.json"

echo "Generated $ROOT_DIR/catalog.json"
