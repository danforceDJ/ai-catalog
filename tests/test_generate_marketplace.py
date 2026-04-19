from __future__ import annotations
import importlib.util
import json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_build_marketplace_from_fixtures(fixtures_dir, tmp_path):
    root = tmp_path
    (root / "plugins").symlink_to(fixtures_dir / "plugins")
    (root / "marketplace.config.json").write_text(
        (fixtures_dir / "marketplace.config.json").read_text()
    )

    mod = _load("generate_marketplace")
    result = mod.build_marketplace(root)

    assert result["name"] == "fixture-marketplace"
    assert result["owner"]["name"] == "fixture-owner"
    names = [p["name"] for p in result["plugins"]]
    assert names == sorted(names), "plugins must be sorted by name"
    assert set(names) == {"fixture-agent", "fixture-bundle", "fixture-mcp",
                          "fixture-prompt", "fixture-skill"}
    bundle = next(p for p in result["plugins"] if p["name"] == "fixture-bundle")
    assert bundle["source"] == "plugins/fixture-bundle"
    assert bundle["version"] == "1.0.0"
    assert bundle["skills"] == "skills"
    assert bundle["mcpServers"] == ".mcp.json"
