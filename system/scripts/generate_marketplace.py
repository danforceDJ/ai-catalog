#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate .github/plugin/marketplace.json from plugins/ + marketplace.config.json."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import shutil

REPO_ROOT = Path(__file__).resolve().parents[2]

PASSTHROUGH_FIELDS = (
    "description", "version", "author", "homepage", "repository",
    "license", "keywords", "category", "tags",
    "skills", "agents", "commands", "hooks", "lspServers",
)


def load_mcp_servers(repo_root: Path, names: list[str]) -> dict:
    """Resolve a list of MCP server names to their actual server config objects."""
    merged: dict = {}
    for name in names:
        mcp_path = repo_root / "catalog" / "mcp" / name / ".mcp.json"
        if mcp_path.is_file():
            data = json.loads(mcp_path.read_text())
            merged.update(data.get("servers", {}))
    return merged


def _is_list_reference_plugin(manifest: dict) -> bool:
    return any(isinstance(manifest.get(field), list) for field in ("skills", "agents", "commands", "mcpServers"))


def _write_compatibility_plugin(repo_root: Path, plugin_dir: Path, manifest: dict) -> Path:
    compat_dir = plugin_dir / ".copilot-plugin"
    if compat_dir.exists():
        shutil.rmtree(compat_dir)
    compat_dir.mkdir(parents=True, exist_ok=True)

    compat_manifest = copy.deepcopy(manifest)

    skills = manifest.get("skills")
    if isinstance(skills, list):
        for name in skills:
            src = repo_root / "catalog" / "skills" / name / "SKILL.md"
            if src.is_file():
                dst = compat_dir / "skills" / name / "SKILL.md"
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        compat_manifest["skills"] = "skills"

    agents = manifest.get("agents")
    if isinstance(agents, list):
        for name in agents:
            src = repo_root / "catalog" / "agents" / f"{name}.agent.md"
            if src.is_file():
                dst = compat_dir / "agents" / src.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        compat_manifest["agents"] = "agents"

    commands = manifest.get("commands")
    if isinstance(commands, list):
        for name in commands:
            src = repo_root / "catalog" / "prompts" / f"{name}.md"
            if src.is_file():
                dst = compat_dir / "commands" / src.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        compat_manifest["commands"] = "commands"

    mcp = manifest.get("mcpServers")
    if isinstance(mcp, list):
        servers = load_mcp_servers(repo_root, mcp)
        (compat_dir / ".mcp.json").write_text(json.dumps({"servers": servers}, indent=2, ensure_ascii=False) + "\n")
        compat_manifest["mcpServers"] = ".mcp.json"

    (compat_dir / "plugin.json").write_text(json.dumps(compat_manifest, indent=2, ensure_ascii=False) + "\n")
    return compat_dir


def _auto_create_plugin_from_mcp(repo_root: Path) -> list[Path]:
    """For every catalog/mcp/<name>/.mcp.json that has x-catalog metadata but no
    corresponding catalog/plugins/<name>/plugin.json, auto-generate plugin.json.
    Returns list of plugin dirs that were created."""
    created: list[Path] = []
    mcp_root = repo_root / "catalog" / "mcp"
    plugins_root = repo_root / "catalog" / "plugins"
    if not mcp_root.is_dir():
        return created
    for mcp_dir in sorted(mcp_root.iterdir()):
        mcp_path = mcp_dir / ".mcp.json"
        if not mcp_dir.is_dir() or not mcp_path.is_file():
            continue
        plugin_path = plugins_root / mcp_dir.name / "plugin.json"
        if plugin_path.exists():
            continue  # already has a plugin wrapper – nothing to do
        try:
            cfg = json.loads(mcp_path.read_text())
        except json.JSONDecodeError:
            continue
        xcatalog = cfg.get("x-catalog")
        if not xcatalog:
            continue  # no metadata – skip (won't be Copilot-installable)
        manifest = {
            "name": mcp_dir.name,
            "description": xcatalog.get("description", f"{mcp_dir.name} MCP server."),
            "version": xcatalog.get("version", "1.0.0"),
            "license": xcatalog.get("license", "MIT"),
            "keywords": xcatalog.get("keywords", [mcp_dir.name]),
            "category": xcatalog.get("category", "integrations"),
            "tags": xcatalog.get("tags", [mcp_dir.name, "mcp"]),
            "mcpServers": [mcp_dir.name],
        }
        if xcatalog.get("author"):
            manifest["author"] = {"name": xcatalog["author"]}
        plugin_path.parent.mkdir(parents=True, exist_ok=True)
        plugin_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        print(f"  [auto-generated] {plugin_path.relative_to(repo_root)}")
        created.append(plugin_path.parent)
    return created


def build_marketplace(repo_root: Path) -> dict:
    # Auto-create plugin.json wrappers for any mcp with x-catalog metadata
    _auto_create_plugin_from_mcp(repo_root)

    config = json.loads((repo_root / "system" / "config" / "marketplace.config.json").read_text())
    plugins_dir = repo_root / "catalog" / "plugins"
    entries: list[dict] = []
    if plugins_dir.is_dir():
        for plugin_dir in sorted(plugins_dir.iterdir()):
            manifest_path = plugin_dir / "plugin.json"
            if not plugin_dir.is_dir() or not manifest_path.is_file():
                continue
            manifest = json.loads(manifest_path.read_text())
            source_dir = plugin_dir
            entry_manifest = manifest
            if _is_list_reference_plugin(manifest):
                source_dir = _write_compatibility_plugin(repo_root, plugin_dir, manifest)
                entry_manifest = json.loads((source_dir / "plugin.json").read_text())
            entry: dict = {
                "name": entry_manifest["name"],
                "source": str(source_dir.relative_to(repo_root)),
            }
            for field in PASSTHROUGH_FIELDS:
                if field in entry_manifest:
                    entry[field] = entry_manifest[field]
            # Resolve mcpServers name list → actual server config objects
            if "mcpServers" in entry_manifest:
                mcp_val = entry_manifest["mcpServers"]
                if isinstance(mcp_val, list):
                    resolved = load_mcp_servers(repo_root, mcp_val)
                    entry["mcpServers"] = resolved if resolved else mcp_val
                else:
                    entry["mcpServers"] = mcp_val
            entries.append(entry)
    return {
        "name": config["name"],
        "owner": config["owner"],
        "metadata": config.get("metadata", {}),
        "plugins": entries,
    }


def main() -> None:
    marketplace = build_marketplace(REPO_ROOT)
    out = REPO_ROOT / ".github" / "plugin" / "marketplace.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out.relative_to(REPO_ROOT)} ({len(marketplace['plugins'])} plugins)")


if __name__ == "__main__":
    main()
