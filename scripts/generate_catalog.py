#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Generate catalog.json (search index) from plugins/ and templates/."""
from __future__ import annotations
import base64
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
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


def plugin_components(plugin_dir: Path, manifest: dict) -> dict:
    skills_path = plugin_dir / _first(manifest.get("skills", "skills"), "skills")
    agents_path = plugin_dir / _first(manifest.get("agents", "agents"), "agents")
    commands_path = plugin_dir / _first(manifest.get("commands", "commands"), "commands")
    mcp_value = manifest.get("mcpServers", ".mcp.json")
    hooks_value = manifest.get("hooks", "hooks.json")
    mcp_path = plugin_dir / mcp_value if isinstance(mcp_value, str) else None
    hooks_path = plugin_dir / hooks_value if isinstance(hooks_value, str) else None

    skills = sorted(s.name for s in skills_path.iterdir() if s.is_dir() and (s / "SKILL.md").is_file()) \
        if skills_path.is_dir() else []
    agents = sorted(p.stem.removesuffix(".agent") for p in agents_path.glob("*.agent.md")) \
        if agents_path.is_dir() else []
    commands = sorted(p.stem for p in commands_path.glob("*.md")) \
        if commands_path.is_dir() else []
    mcp_servers: list[str] = []
    if mcp_path and mcp_path.is_file():
        try:
            cfg = json.loads(mcp_path.read_text())
            mcp_servers = sorted((cfg.get("servers") or {}).keys())
        except json.JSONDecodeError:
            mcp_servers = []
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


def build_deeplink(plugin_dir: Path, manifest: dict) -> str | None:
    mcp_value = manifest.get("mcpServers", ".mcp.json")
    if not isinstance(mcp_value, str):
        return None
    mcp_path = plugin_dir / mcp_value
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
    encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return f"vscode:mcp/install?name={name}&config={encoded}"


def raw_files(plugin_dir: Path, components: dict) -> list[str]:
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


def build_plugin_entry(plugin_dir: Path) -> dict | None:
    manifest_path = plugin_dir / "plugin.json"
    if not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text())
    components = plugin_components(plugin_dir, manifest)
    entry_type = derive_type(components)
    deeplink = build_deeplink(plugin_dir, manifest) if components["mcpServers"] else None
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
            "vscodeMcpDeeplink": deeplink,
            "rawFiles": raw_files(plugin_dir, components),
            "zip": f"dl/{plugin_dir.name}.zip",
            "repoPath": f"plugins/{plugin_dir.name}",
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
            "repoPath": f"templates/{template_dir.name}",
        },
    }


def build_catalog(repo_root: Path) -> dict:
    plugins: list[dict] = []
    plugins_dir = repo_root / "plugins"
    if plugins_dir.is_dir():
        for d in sorted(plugins_dir.iterdir()):
            if d.is_dir():
                entry = build_plugin_entry(d)
                if entry:
                    plugins.append(entry)
    templates: list[dict] = []
    templates_dir = repo_root / "templates"
    if templates_dir.is_dir():
        for d in sorted(templates_dir.iterdir()):
            if d.is_dir():
                entry = build_template_entry(d)
                if entry:
                    templates.append(entry)
    return {
        "generated_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plugins": plugins,
        "templates": templates,
    }


def main() -> None:
    catalog = build_catalog(REPO_ROOT)
    payload = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    (REPO_ROOT / "catalog.json").write_text(payload)
    docs_copy = REPO_ROOT / "docs" / "catalog.json"
    docs_copy.parent.mkdir(parents=True, exist_ok=True)
    docs_copy.write_text(payload)
    print(f"Wrote catalog.json ({len(catalog['plugins'])} plugins, {len(catalog['templates'])} templates)")


if __name__ == "__main__":
    main()
