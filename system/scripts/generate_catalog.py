#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Generate catalog.json (search index) from plugins/ and templates/."""
from __future__ import annotations
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
DEEPLINK_MAX_BYTES = 2048


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def _first(value: Any, default: str) -> str:
    if isinstance(value, list):
        return value[0] if value else default
    if isinstance(value, str):
        return value
    return default


def _resolve_mcp_servers(mcp_paths: list[Path]) -> list[str]:
    servers: list[str] = []
    for p in mcp_paths:
        if p.is_file():
            try:
                cfg = json.loads(p.read_text())
                servers.extend(sorted((cfg.get("servers") or {}).keys()))
            except json.JSONDecodeError:
                pass
    return sorted(servers)


def plugin_components(plugin_dir: Path, manifest: dict, repo_root: Path | None = None) -> dict:
    skills_value = manifest.get("skills", "skills")
    agents_value = manifest.get("agents", "agents")
    commands_value = manifest.get("commands", "commands")
    mcp_value = manifest.get("mcpServers", ".mcp.json")
    hooks_value = manifest.get("hooks", "hooks.json")

    # Skills: list of top-level names or a string path relative to plugin_dir
    if isinstance(skills_value, list) and repo_root is not None:
        skills = [n for n in skills_value if (repo_root / "catalog" / "skills" / n / "SKILL.md").is_file()]
    else:
        skills_path = plugin_dir / _first(skills_value, "skills")
        skills = sorted(s.name for s in skills_path.iterdir() if s.is_dir() and (s / "SKILL.md").is_file()) \
            if skills_path.is_dir() else []

    # Agents: list of top-level names or a string path relative to plugin_dir
    if isinstance(agents_value, list) and repo_root is not None:
        agents = [n for n in agents_value if (repo_root / "catalog" / "agents" / f"{n}.agent.md").is_file()]
    else:
        agents_path = plugin_dir / _first(agents_value, "agents")
        agents = sorted(p.stem.removesuffix(".agent") for p in agents_path.glob("*.agent.md")) \
            if agents_path.is_dir() else []

    # Commands: list of top-level names or a string path relative to plugin_dir
    if isinstance(commands_value, list) and repo_root is not None:
        commands = [n for n in commands_value if (repo_root / "catalog" / "prompts" / f"{n}.md").is_file()]
    else:
        commands_path = plugin_dir / _first(commands_value, "commands")
        commands = sorted(p.stem for p in commands_path.glob("*.md")) \
            if commands_path.is_dir() else []

    # MCP servers: list of top-level dir names or a string .mcp.json path relative to plugin_dir
    if isinstance(mcp_value, list) and repo_root is not None:
        mcp_paths = [repo_root / "catalog" / "mcp" / name / ".mcp.json" for name in mcp_value]
    elif isinstance(mcp_value, str):
        mcp_paths = [plugin_dir / mcp_value]
    else:
        mcp_paths = []
    mcp_servers = _resolve_mcp_servers(mcp_paths)

    hooks_path = plugin_dir / (hooks_value if isinstance(hooks_value, str) else "hooks.json")
    return {
        "skills": skills,
        "agents": agents,
        "commands": commands,
        "mcpServers": mcp_servers,
        "hooks": bool(hooks_path and hooks_path.is_file()),
    }


def derive_type(components: dict) -> str:
    kinds = [k for k, v in {
        "mcp": components["mcpServers"],
        "skill": components["skills"],
        "agent": components["agents"],
        "prompt": components["commands"],
    }.items() if v]
    if len(kinds) >= 2:
        return "bundle"
    if len(kinds) == 1:
        return kinds[0]
    return "empty"


def build_deeplink(plugin_dir: Path, manifest: dict, repo_root: Path | None = None) -> str | None:
    mcp_value = manifest.get("mcpServers", ".mcp.json")
    if isinstance(mcp_value, list) and repo_root is not None:
        if len(mcp_value) != 1:
            return None
        mcp_path = repo_root / "catalog" / "mcp" / mcp_value[0] / ".mcp.json"
    elif isinstance(mcp_value, str):
        mcp_path = plugin_dir / mcp_value
    else:
        return None
    if not mcp_path.is_file():
        return None
    try:
        cfg = json.loads(mcp_path.read_text())
    except json.JSONDecodeError:
        return None
    servers = cfg.get("servers") or {}
    if not servers:
        return None
    name, server_cfg = next(iter(servers.items()))
    payload = json.dumps({"name": name, **server_cfg}, separators=(",", ":"))
    if len(payload.encode()) > DEEPLINK_MAX_BYTES:
        return None
    encoded = urllib.parse.quote(payload, safe="")
    return f"vscode:mcp/install?config={encoded}"


def raw_files(plugin_dir: Path, components: dict, manifest: dict | None = None) -> list[str]:
    # List-reference plugins: standalone primitive entries carry raw files; wrapper has none
    if manifest is not None:
        if isinstance(manifest.get("skills"), list) or isinstance(manifest.get("agents"), list) \
                or isinstance(manifest.get("commands"), list):
            return []
    kinds_with_items = sum(1 for k in ("skills", "agents", "commands") if components[k])
    if kinds_with_items != 1 or components["mcpServers"]:
        return []
    if len(components["skills"]) == 1:
        skill = plugin_dir / "skills" / components["skills"][0] / "SKILL.md"
        return [str(skill.relative_to(plugin_dir))] if skill.is_file() else []
    if len(components["agents"]) == 1:
        files = list((plugin_dir / "agents").glob("*.agent.md"))
        return [str(f.relative_to(plugin_dir)) for f in files]
    if len(components["commands"]) == 1:
        files = list((plugin_dir / "commands").glob("*.md"))
        return [str(f.relative_to(plugin_dir)) for f in files]
    return []


def build_platform_fields(name: str, components: dict) -> dict:
    """Return claude, platforms, and vscodeWorkspace install fields.
    
    Args:
        name: Entry name for the claude install command
        components: Component dict with keys: skills, agents, commands, mcpServers, hooks
    
    Returns:
        Dict with keys: claude, platforms, vscodeWorkspace
    """
    has_mcp = bool(components.get("mcpServers"))
    has_commands = bool(components.get("commands"))
    has_agents = bool(components.get("agents"))
    
    # Claude install command if plugin has MCP, commands, or agents
    claude_install = f"claude plugin install {name}" if (has_mcp or has_commands or has_agents) else None
    
    # Platforms list
    platforms = ["copilot-cli"]
    if has_mcp or has_commands or has_agents:
        platforms.append("claude")
    if has_mcp:
        platforms.append("vscode")
    
    # VS Code workspace config path
    vscode_workspace = ".vscode/mcp.json" if has_mcp else None
    
    return {
        "claude": claude_install,
        "platforms": platforms,
        "vscodeWorkspace": vscode_workspace,
    }


def build_plugin_entry(plugin_dir: Path, repo_root: Path | None = None) -> dict | None:
    manifest_path = plugin_dir / "plugin.json"
    if not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text())
    components = plugin_components(plugin_dir, manifest, repo_root)
    entry_type = derive_type(components)
    deeplink = build_deeplink(plugin_dir, manifest, repo_root) if components["mcpServers"] else None
    return {
        "name": manifest["name"],
        "description": manifest.get("description", ""),
        "version": manifest.get("version", ""),
        "type": entry_type,
        "category": manifest.get("category", ""),
        "tags": manifest.get("tags", []),
        "keywords": manifest.get("keywords", []),
        "components": components,
        "install": {
            "copilot": f"{manifest['name']}@ai-catalog",
            **build_platform_fields(manifest["name"], components),
            "vscodeMcpDeeplink": deeplink,
            "rawFiles": raw_files(plugin_dir, components, manifest),
            "zip": f"dl/{plugin_dir.name}.zip",
            "repoPath": f"catalog/plugins/{plugin_dir.name}",
        },
    }


def build_template_entry(template_dir: Path) -> dict | None:
    tpl = template_dir / "TEMPLATE.md"
    if not tpl.is_file():
        return None
    fm = parse_frontmatter(tpl.read_text())
    return {
        "name": fm.get("name", template_dir.name),
        "description": fm.get("description", ""),
        "version": fm.get("version", ""),
        "type": "template",
        "category": fm.get("category", ""),
        "tags": fm.get("tags", []) or [],
        "keywords": fm.get("keywords", []) or [],
        "install": {
            "rawFiles": ["TEMPLATE.md"],
            "zip": f"dl/{template_dir.name}.zip",
            "repoPath": f"catalog/templates/{template_dir.name}",
        },
    }


def _deeplink_from_mcp_path(mcp_path: Path) -> str | None:
    if not mcp_path.is_file():
        return None
    try:
        cfg = json.loads(mcp_path.read_text())
    except json.JSONDecodeError:
        return None
    servers = cfg.get("servers") or {}
    if not servers:
        return None
    name, server_cfg = next(iter(servers.items()))
    payload = json.dumps({"name": name, **server_cfg}, separators=(",", ":"))
    if len(payload.encode()) > DEEPLINK_MAX_BYTES:
        return None
    encoded = urllib.parse.quote(payload, safe="")
    return f"vscode:mcp/install?config={encoded}"


def build_top_level_entries(
    repo_root: Path,
    covered_skills: set[str],
    covered_agents: set[str],
    covered_commands: set[str],
    covered_mcp_dirs: set[str] | None = None,
) -> list[dict]:
    """Build catalog entries for top-level primitives not already wrapped by a plugin."""
    entries: list[dict] = []

    # Standalone skills
    skills_dir = repo_root / "catalog" / "skills"
    if skills_dir.is_dir():
        for skill_dir in sorted(d for d in skills_dir.iterdir() if d.is_dir()):
            if skill_dir.name in covered_skills:
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue
            fm = parse_frontmatter(skill_md.read_text())
            components = {"skills": [skill_dir.name], "agents": [], "commands": [], "mcpServers": [], "hooks": False}
            entries.append({
                "name": fm.get("name", skill_dir.name),
                "description": fm.get("description", ""),
                "version": fm.get("version", ""),
                "type": "skill",
                "category": fm.get("category", ""),
                "tags": fm.get("tags", []) or [],
                "keywords": fm.get("keywords", []) or [],
                "components": components,
                "install": {
                    "copilot": None,
                    **build_platform_fields(skill_dir.name, components),
                    "vscodeMcpDeeplink": None,
                    "rawFiles": ["SKILL.md"],
                    "zip": f"dl/{skill_dir.name}.zip",
                    "repoPath": f"catalog/skills/{skill_dir.name}",
                },
            })

    # Standalone agents
    agents_dir = repo_root / "catalog" / "agents"
    if agents_dir.is_dir():
        for agent_path in sorted(agents_dir.glob("*.agent.md")):
            agent_name = agent_path.stem.removesuffix(".agent")
            if agent_name in covered_agents:
                continue
            fm = parse_frontmatter(agent_path.read_text())
            components = {"skills": [], "agents": [agent_name], "commands": [], "mcpServers": [], "hooks": False}
            entries.append({
                "name": fm.get("name", agent_name),
                "description": fm.get("description", ""),
                "version": fm.get("version", ""),
                "type": "agent",
                "category": fm.get("category", ""),
                "tags": fm.get("tags", []) or [],
                "keywords": fm.get("keywords", []) or [],
                "components": components,
                "install": {
                    "copilot": None,
                    **build_platform_fields(agent_name, components),
                    "vscodeMcpDeeplink": None,
                    "rawFiles": [agent_path.name],
                    "zip": f"dl/{agent_name}.zip",
                    "repoPath": "catalog/agents",
                },
            })

    # Standalone commands
    commands_dir = repo_root / "catalog" / "prompts"
    if commands_dir.is_dir():
        for cmd_path in sorted(commands_dir.glob("*.md")):
            cmd_name = cmd_path.stem
            if cmd_name in covered_commands:
                continue
            fm = parse_frontmatter(cmd_path.read_text())
            components = {"skills": [], "agents": [], "commands": [cmd_name], "mcpServers": [], "hooks": False}
            entries.append({
                "name": fm.get("name", cmd_name),
                "description": fm.get("description", ""),
                "version": fm.get("version", ""),
                "type": "prompt",
                "category": fm.get("category", ""),
                "tags": fm.get("tags", []) or [],
                "keywords": fm.get("keywords", []) or [],
                "components": components,
                "install": {
                    "copilot": None,
                    **build_platform_fields(cmd_name, components),
                    "vscodeMcpDeeplink": None,
                    "rawFiles": [cmd_path.name],
                    "zip": f"dl/{cmd_name}.zip",
                    "repoPath": "catalog/prompts",
                },
            })

    # Standalone MCP server configs
    mcp_dir = repo_root / "catalog" / "mcp"
    if mcp_dir.is_dir():
        for mcp_server_dir in sorted(d for d in mcp_dir.iterdir() if d.is_dir()):
            if covered_mcp_dirs and mcp_server_dir.name in covered_mcp_dirs:
                continue
            mcp_path = mcp_server_dir / ".mcp.json"
            if not mcp_path.is_file():
                continue
            try:
                cfg = json.loads(mcp_path.read_text())
            except json.JSONDecodeError:
                continue
            server_names = sorted((cfg.get("servers") or {}).keys())
            if not server_names:
                continue
            deeplink = _deeplink_from_mcp_path(mcp_path)
            components = {"skills": [], "agents": [], "commands": [], "mcpServers": server_names, "hooks": False}
            entries.append({
                "name": mcp_server_dir.name,
                "description": "",
                "version": "",
                "type": "mcp",
                "category": "",
                "tags": [],
                "keywords": [],
                "components": components,
                "install": {
                    "copilot": None,
                    **build_platform_fields(mcp_server_dir.name, components),
                    "vscodeMcpDeeplink": deeplink,
                    "rawFiles": [],
                    "zip": f"dl/{mcp_server_dir.name}.zip",
                    "repoPath": f"catalog/mcp/{mcp_server_dir.name}",
                },
            })

    return entries


def build_catalog(repo_root: Path) -> dict:
    plugins: list[dict] = []
    plugins_dir = repo_root / "catalog" / "plugins"
    if plugins_dir.is_dir():
        for d in sorted(plugins_dir.iterdir()):
            if d.is_dir():
                entry = build_plugin_entry(d, repo_root)
                if entry:
                    plugins.append(entry)

    # Collect primitives already covered by plugin wrappers
    covered_skills: set[str] = set()
    covered_agents: set[str] = set()
    covered_commands: set[str] = set()
    covered_mcp_dirs: set[str] = set()
    for entry in plugins:
        covered_skills.update(entry["components"]["skills"])
        covered_agents.update(entry["components"]["agents"])
        covered_commands.update(entry["components"]["commands"])
    # Track which catalog/mcp/<name> dirs are already wrapped by a plugin via list-reference
    if plugins_dir.is_dir():
        for d in sorted(plugins_dir.iterdir()):
            manifest_path = d / "plugin.json"
            if d.is_dir() and manifest_path.is_file():
                try:
                    manifest = json.loads(manifest_path.read_text())
                    mcp_value = manifest.get("mcpServers")
                    if isinstance(mcp_value, list):
                        covered_mcp_dirs.update(mcp_value)
                except (json.JSONDecodeError, KeyError):
                    pass

    # Add standalone catalog entries for uncovered top-level primitives
    standalone = build_top_level_entries(repo_root, covered_skills, covered_agents, covered_commands, covered_mcp_dirs)
    plugins.extend(standalone)
    plugins.sort(key=lambda p: p["name"])

    templates: list[dict] = []
    templates_dir = repo_root / "catalog" / "templates"
    if templates_dir.is_dir():
        for d in sorted(templates_dir.iterdir()):
            if d.is_dir():
                entry = build_template_entry(d)
                if entry:
                    templates.append(entry)
    return {
        "plugins": plugins,
        "templates": templates,
    }


def main() -> None:
    catalog = build_catalog(REPO_ROOT)
    payload = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    (REPO_ROOT / "system" / "artifacts" / "catalog.json").write_text(payload)
    print(f"Wrote system/artifacts/catalog.json ({len(catalog['plugins'])} plugins/primitives, {len(catalog['templates'])} templates)")


if __name__ == "__main__":
    main()
