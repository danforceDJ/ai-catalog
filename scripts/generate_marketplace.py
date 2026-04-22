#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate .github/plugin/marketplace.json from plugins/ + marketplace.config.json."""
from __future__ import annotations
import json
from pathlib import Path
import shutil

REPO_ROOT = Path(__file__).resolve().parents[1]

PASSTHROUGH_FIELDS = (
    "description", "version", "author", "homepage", "repository",
    "license", "keywords", "category", "tags",
    "skills", "agents", "commands", "hooks", "lspServers",
)


def load_mcp_servers(repo_root: Path, names: list[str]) -> dict:
    """Resolve a list of MCP server names to their actual server config objects."""
    merged: dict = {}
    for name in names:
        mcp_path = repo_root / "mcpServers" / name / ".mcp.json"
        if mcp_path.is_file():
            data = json.loads(mcp_path.read_text())
            merged.update(data.get("servers", {}))
    return merged


def _is_list_ref_plugin(manifest: dict) -> bool:
    return any(isinstance(manifest.get(field), list) for field in ("skills", "agents", "commands", "mcpServers"))


def _write_compat_plugin(repo_root: Path, plugin_dir: Path, manifest: dict) -> Path:
    compat_dir = plugin_dir / ".copilot-plugin"
    if compat_dir.exists():
        shutil.rmtree(compat_dir)
    compat_dir.mkdir(parents=True, exist_ok=True)

    compat_manifest = dict(manifest)

    skills = manifest.get("skills")
    if isinstance(skills, list):
        for name in skills:
            src = repo_root / "skills" / name / "SKILL.md"
            if src.is_file():
                dst = compat_dir / "skills" / name / "SKILL.md"
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        compat_manifest["skills"] = "skills"

    agents = manifest.get("agents")
    if isinstance(agents, list):
        for name in agents:
            src = repo_root / "agents" / f"{name}.agent.md"
            if src.is_file():
                dst = compat_dir / "agents" / src.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        compat_manifest["agents"] = "agents"

    commands = manifest.get("commands")
    if isinstance(commands, list):
        for name in commands:
            src = repo_root / "commands" / f"{name}.md"
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


def build_marketplace(repo_root: Path) -> dict:
    config = json.loads((repo_root / "marketplace.config.json").read_text())
    plugins_dir = repo_root / "plugins"
    entries: list[dict] = []
    if plugins_dir.is_dir():
        for plugin_dir in sorted(plugins_dir.iterdir()):
            manifest_path = plugin_dir / "plugin.json"
            if not plugin_dir.is_dir() or not manifest_path.is_file():
                continue
            manifest = json.loads(manifest_path.read_text())
            source_dir = plugin_dir
            entry_manifest = manifest
            if _is_list_ref_plugin(manifest):
                source_dir = _write_compat_plugin(repo_root, plugin_dir, manifest)
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
