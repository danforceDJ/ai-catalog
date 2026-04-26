from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import shutil

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_build_marketplace_from_fixtures(fixtures_dir, tmp_path):
    root = tmp_path
    catalog_dir = root / "catalog"
    catalog_dir.mkdir()
    shutil.copytree(fixtures_dir / "catalog" / "plugins", catalog_dir / "plugins")
    for name, newname in [("skills", "skills"), ("agents", "agents"), ("commands", "prompts"), ("mcpServers", "mcp")]:
        src = fixtures_dir / "catalog" / newname
        if src.exists():
            shutil.copytree(src, catalog_dir / newname)
    config_dir = root / "system" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "marketplace.config.json").write_text(
        (fixtures_dir / "marketplace.config.json").read_text()
    )

    mod = _load("generate_marketplace")
    result = mod.build_marketplace(root)

    assert result["name"] == "fixture-marketplace"
    assert result["owner"]["name"] == "fixture-owner"
    names = [p["name"] for p in result["plugins"]]
    assert names == sorted(names), "plugins must be sorted by name"
    assert set(names) == {"fixture-agent", "fixture-bundle", "fixture-list-bundle", "fixture-mcp",
                          "fixture-prompt", "fixture-skill"}
    bundle = next(p for p in result["plugins"] if p["name"] == "fixture-bundle")
    assert bundle["source"] == "catalog/plugins/fixture-bundle"
    assert bundle["version"] == "1.0.0"
    assert bundle["skills"] == "skills"
    assert bundle["mcpServers"] == ".mcp.json"
    list_bundle = next(p for p in result["plugins"] if p["name"] == "fixture-list-bundle")
    assert list_bundle["source"] == "catalog/plugins/fixture-list-bundle/.copilot-plugin"
    assert list_bundle["skills"] == "skills"
    assert list_bundle["mcpServers"] == ".mcp.json"
    generated_plugin = root / "catalog" / "plugins" / "fixture-list-bundle" / ".copilot-plugin" / "plugin.json"
    generated_mcp = root / "catalog" / "plugins" / "fixture-list-bundle" / ".copilot-plugin" / ".mcp.json"
    assert generated_plugin.is_file()
    assert generated_mcp.is_file()
    assert json.loads(generated_mcp.read_text())["servers"] == {
        "fixture-top-server": {"command": "echo", "args": ["top"]}
    }
