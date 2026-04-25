#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Generate Claude Code marketplace artifacts (claude.marketplace.json + claude-plugin.json per plugin)."""
from __future__ import annotations
import copy
import json
import re
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

PASSTHROUGH_FIELDS = (
    "description", "version", "author", "homepage", "repository",
    "license", "keywords", "category", "tags",
)


def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from markdown files."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def load_mcp_servers(repo_root: Path, names: list[str]) -> dict:
    """Resolve a list of MCP server names to their actual server config objects."""
    merged: dict = {}
    for name in names:
        mcp_path = repo_root / "catalog" / "mcp" / name / ".mcp.json"
        if mcp_path.is_file():
            data = json.loads(mcp_path.read_text())
            merged.update(data.get("servers", {}))
    return merged


def load_mcp_inline(mcp_path: Path) -> dict:
    """Load MCP servers from a local .mcp.json file and transform to Claude format."""
    if not mcp_path.is_file():
        return {}
    data = json.loads(mcp_path.read_text())
    servers = data.get("servers", {})
    
    # Transform each server: drop 'type', keep 'command', 'args', 'env'
    transformed: dict = {}
    for server_name, server_config in servers.items():
        claude_config = {}
        for key in ("command", "args", "env"):
            if key in server_config:
                claude_config[key] = server_config[key]
        if claude_config:
            transformed[server_name] = claude_config
    return transformed


def resolve_commands(manifest: dict, plugin_dir: Path, repo_root: Path) -> list[dict]:
    """Resolve commands from manifest into list of {name, description, prompt} dicts."""
    commands_value = manifest.get("commands")
    if not commands_value:
        return []
    
    command_names: list[str] = []
    
    if isinstance(commands_value, list):
        # List reference: look in repo_root / "commands" / f"{name}.md"
        for name in commands_value:
            cmd_path = repo_root / "catalog" / "prompts" / f"{name}.md"
            if cmd_path.is_file():
                command_names.append(name)
    elif isinstance(commands_value, str):
        # String path: look in plugin_dir / commands_value / "*.md"
        cmd_dir = plugin_dir / commands_value
        if cmd_dir.is_dir():
            for cmd_file in sorted(cmd_dir.glob("*.md")):
                command_names.append(cmd_file.stem)
    
    result: list[dict] = []
    for name in command_names:
        # Determine path based on reference type
        if isinstance(commands_value, list):
            cmd_path = repo_root / "catalog" / "prompts" / f"{name}.md"
            prompt_path = f"commands/{name}.md"
        else:
            cmd_path = plugin_dir / commands_value / f"{name}.md"
            prompt_path = f"commands/{name}.md"
        
        description = ""
        if cmd_path.is_file():
            frontmatter = parse_frontmatter(cmd_path.read_text())
            description = frontmatter.get("description", "")
        
        result.append({
            "name": name,
            "description": description,
            "prompt": prompt_path,
        })
    
    return result


def resolve_agents(manifest: dict, plugin_dir: Path, repo_root: Path) -> str | list[str] | None:
    """Resolve agents from manifest into instructions path(s)."""
    agents_value = manifest.get("agents")
    if not agents_value:
        return None
    
    agent_names: list[str] = []
    
    if isinstance(agents_value, list):
        # List reference: look in repo_root / "agents" / f"{name}.agent.md"
        for name in agents_value:
            agent_path = repo_root / "catalog" / "agents" / f"{name}.agent.md"
            if agent_path.is_file():
                agent_names.append(name)
    elif isinstance(agents_value, str):
        # String path: look in plugin_dir / agents_value / "*.agent.md"
        agent_dir = plugin_dir / agents_value
        if agent_dir.is_dir():
            for agent_file in sorted(agent_dir.glob("*.agent.md")):
                agent_names.append(agent_file.stem.removesuffix(".agent"))
    
    if not agent_names:
        return None
    
    if len(agent_names) == 1:
        return f"agents/{agent_names[0]}.agent.md"
    else:
        return [f"agents/{name}.agent.md" for name in agent_names]


def resolve_mcp_servers(manifest: dict, plugin_dir: Path, repo_root: Path) -> dict:
    """Resolve MCP servers from manifest into Claude format (no 'type' field)."""
    mcp_value = manifest.get("mcpServers")
    if not mcp_value:
        return {}
    
    if isinstance(mcp_value, list):
        # List reference: load from mcpServers/<name>/.mcp.json
        servers = load_mcp_servers(repo_root, mcp_value)
        # Transform: drop 'type' field
        transformed: dict = {}
        for server_name, server_config in servers.items():
            claude_config = {}
            for key in ("command", "args", "env"):
                if key in server_config:
                    claude_config[key] = server_config[key]
            if claude_config:
                transformed[server_name] = claude_config
        return transformed
    elif isinstance(mcp_value, str):
        # String path: load from plugin_dir / mcp_value
        return load_mcp_inline(plugin_dir / mcp_value)
    elif isinstance(mcp_value, dict):
        # Inline object: use directly, dropping 'type' from each server
        transformed: dict = {}
        for server_name, server_config in mcp_value.items():
            claude_config = {}
            for key in ("command", "args", "env"):
                if key in server_config:
                    claude_config[key] = server_config[key]
            if claude_config:
                transformed[server_name] = claude_config
        return transformed
    
    return {}


def materialize_claude_plugin(repo_root: Path, plugin_dir: Path, manifest: dict, claude_manifest: dict) -> Path:
    """Create .claude-plugin/ directory with materialized files and manifest."""
    claude_dir = plugin_dir / ".claude-plugin"
    if claude_dir.exists():
        import shutil
        shutil.rmtree(claude_dir)
    claude_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy referenced files
    commands_value = manifest.get("commands")
    if isinstance(commands_value, list):
        # Copy from repo_root / "commands" / f"{name}.md"
        for name in commands_value:
            src = repo_root / "catalog" / "prompts" / f"{name}.md"
            if src.is_file():
                dst = claude_dir / "commands" / f"{name}.md"
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(src.read_text())
    elif isinstance(commands_value, str):
        # Copy from plugin_dir / commands_value / "*.md"
        src_dir = plugin_dir / commands_value
        if src_dir.is_dir():
            for cmd_file in src_dir.glob("*.md"):
                dst = claude_dir / "commands" / cmd_file.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(cmd_file.read_text())
    
    agents_value = manifest.get("agents")
    if isinstance(agents_value, list):
        # Copy from repo_root / "agents" / f"{name}.agent.md"
        for name in agents_value:
            src = repo_root / "catalog" / "agents" / f"{name}.agent.md"
            if src.is_file():
                dst = claude_dir / "agents" / f"{name}.agent.md"
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(src.read_text())
    elif isinstance(agents_value, str):
        # Copy from plugin_dir / agents_value / "*.agent.md"
        src_dir = plugin_dir / agents_value
        if src_dir.is_dir():
            for agent_file in src_dir.glob("*.agent.md"):
                dst = claude_dir / "agents" / agent_file.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(agent_file.read_text())
    
    # Write materialized manifest
    materialized = copy.deepcopy(claude_manifest)
    (claude_dir / "claude-plugin.json").write_text(json.dumps(materialized, indent=2, ensure_ascii=False) + "\n")
    
    return claude_dir


def build_claude_marketplace(repo_root: Path) -> dict:
    """Build Claude marketplace structure."""
    config = json.loads((repo_root / "system" / "config" / "marketplace.config.json").read_text())
    repo_url = f"https://github.com/{config['owner']['name']}/{config['name']}"
    
    plugins_dir = repo_root / "catalog" / "plugins"
    entries: list[dict] = []
    
    if plugins_dir.is_dir():
        for plugin_dir in sorted(plugins_dir.iterdir()):
            manifest_path = plugin_dir / "plugin.json"
            if not plugin_dir.is_dir() or not manifest_path.is_file():
                continue
            
            manifest = json.loads(manifest_path.read_text())
            plugin_name = manifest.get("name", plugin_dir.name)
            
            # Build Claude plugin manifest
            claude_manifest: dict[str, Any] = {"name": plugin_name}
            
            # Passthrough fields
            for field in PASSTHROUGH_FIELDS:
                if field in manifest:
                    claude_manifest[field] = manifest[field]
            
            # Resolve MCP servers
            mcp_servers = resolve_mcp_servers(manifest, plugin_dir, repo_root)
            if mcp_servers:
                claude_manifest["mcpServers"] = mcp_servers
            
            # Resolve slash commands
            slash_commands = resolve_commands(manifest, plugin_dir, repo_root)
            if slash_commands:
                claude_manifest["slashCommands"] = slash_commands
            
            # Resolve agents as instructions
            agents = resolve_agents(manifest, plugin_dir, repo_root)
            if agents:
                claude_manifest["instructions"] = agents
            
            # Materialize .claude-plugin/ directory
            materialize_claude_plugin(repo_root, plugin_dir, manifest, claude_manifest)
            
            # Write claude-plugin.json at plugin root
            (plugin_dir / "claude-plugin.json").write_text(json.dumps(claude_manifest, indent=2, ensure_ascii=False) + "\n")
            
            # Add to marketplace entries
            entry: dict[str, Any] = {
                "name": plugin_name,
                "source": {
                    "type": "git",
                    "url": repo_url,
                    "path": f"catalog/plugins/{plugin_name}",
                },
                "manifest": "claude-plugin.json",
            }
            
            # Optional fields
            for field in ("category", "tags"):
                if field in manifest:
                    entry[field] = manifest[field]
            
            entries.append(entry)
    
    return {
        "name": config["name"],
        "version": config["metadata"].get("version", "1.0.0"),
        "description": config["metadata"].get("description", ""),
        "plugins": entries,
    }


def main() -> None:
    """Generate Claude marketplace artifacts."""
    marketplace = build_claude_marketplace(REPO_ROOT)
    
    # Write claude.marketplace.json
    out = REPO_ROOT / "system" / "artifacts" / "claude.marketplace.json"
    out.write_text(json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n")
    
    print(f"Wrote {out.relative_to(REPO_ROOT)} ({len(marketplace['plugins'])} plugins)")
    
    # Summary of generated claude-plugin.json files
    plugins_dir = REPO_ROOT / "catalog" / "plugins"
    if plugins_dir.is_dir():
        count = sum(1 for p in plugins_dir.iterdir() if (p / "claude-plugin.json").is_file())
        print(f"Wrote {count} claude-plugin.json files")


if __name__ == "__main__":
    main()
