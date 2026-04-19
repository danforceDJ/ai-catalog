#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate .github/plugin/marketplace.json from plugins/ + marketplace.config.json."""
from __future__ import annotations
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PASSTHROUGH_FIELDS = (
    "description", "version", "author", "homepage", "repository",
    "license", "keywords", "category", "tags",
    "skills", "agents", "commands", "hooks", "mcpServers", "lspServers",
)


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
            entry: dict = {
                "name": manifest["name"],
                "source": f"plugins/{plugin_dir.name}",
            }
            for field in PASSTHROUGH_FIELDS:
                if field in manifest:
                    entry[field] = manifest[field]
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
