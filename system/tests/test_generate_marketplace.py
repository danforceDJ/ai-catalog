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


def test_auto_create_plugin_from_mcp_xcatalog(fixtures_dir, tmp_path):
    """When mcp/<name>/.mcp.json has x-catalog but plugins/<name>/plugin.json
    is absent, build_marketplace() auto-creates the plugin wrapper and produces .copilot-plugin/ output."""
    root = tmp_path

    # Only copy the xcatalog MCP fixture — no plugin.json wrapper exists yet
    mcp_dir = root / "mcp" / "fixture-xcatalog-mcp"
    mcp_dir.mkdir(parents=True)
    shutil.copy2(
        fixtures_dir / "mcp" / "fixture-xcatalog-mcp" / ".mcp.json",
        mcp_dir / ".mcp.json",
    )
    (root / "plugins").mkdir()

    config_dir = root / "system" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "marketplace.config.json").write_text(
        (fixtures_dir / "marketplace.config.json").read_text()
    )

    plugin_json = root / "plugins" / "fixture-xcatalog-mcp" / "plugin.json"
    assert not plugin_json.exists(), "plugin.json must not exist before the run"

    mod = _load("generate_marketplace")
    result = mod.build_marketplace(root)

    # plugin.json was auto-created with correct fields from x-catalog
    assert plugin_json.is_file(), "plugin.json was not auto-created"
    manifest = json.loads(plugin_json.read_text())
    assert manifest["name"] == "fixture-xcatalog-mcp"
    assert manifest["description"] == "A fixture MCP server with x-catalog metadata."
    assert manifest["version"] == "2.3.4"
    assert manifest["category"] == "testing"
    assert manifest["tags"] == ["fixture", "xcatalog"]
    assert manifest["keywords"] == ["test", "metadata"]
    assert manifest["mcpServers"] == ["fixture-xcatalog-mcp"]

    # .copilot-plugin/ output is produced (list-ref plugin → compat dir)
    compat_dir = root / "plugins" / "fixture-xcatalog-mcp" / ".copilot-plugin"
    assert compat_dir.is_dir(), ".copilot-plugin/ directory was not generated"
    compat_mcp = compat_dir / ".mcp.json"
    assert compat_mcp.is_file(), ".copilot-plugin/.mcp.json was not generated"
    servers = json.loads(compat_mcp.read_text())["servers"]
    assert servers == {"fixture-xcatalog-server": {"command": "echo", "args": ["xcatalog"]}}

    # Entry appears in the marketplace output
    names = [p["name"] for p in result["plugins"]]
    assert "fixture-xcatalog-mcp" in names
    entry = next(p for p in result["plugins"] if p["name"] == "fixture-xcatalog-mcp")
    assert entry["source"] == "plugins/fixture-xcatalog-mcp/.copilot-plugin"


def test_auto_create_plugin_skips_mcp_without_xcatalog(fixtures_dir, tmp_path):
    """mcp/<name>/.mcp.json without x-catalog is NOT auto-promoted to a plugin wrapper."""
    root = tmp_path

    mcp_dir = root / "mcp" / "fixture-no-xcatalog-mcp"
    mcp_dir.mkdir(parents=True)
    shutil.copy2(
        fixtures_dir / "mcp" / "fixture-no-xcatalog-mcp" / ".mcp.json",
        mcp_dir / ".mcp.json",
    )
    (root / "plugins").mkdir()

    config_dir = root / "system" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "marketplace.config.json").write_text(
        (fixtures_dir / "marketplace.config.json").read_text()
    )

    mod = _load("generate_marketplace")
    mod.build_marketplace(root)

    plugin_json = root / "plugins" / "fixture-no-xcatalog-mcp" / "plugin.json"
    assert not plugin_json.exists(), "plugin.json must NOT be created when x-catalog is absent"


def test_auto_create_plugin_skips_existing_plugin_json(fixtures_dir, tmp_path):
    """When plugins/<name>/plugin.json already exists, _auto_create_plugin_from_mcp
    leaves it untouched."""
    root = tmp_path

    mcp_dir = root / "mcp" / "fixture-xcatalog-mcp"
    mcp_dir.mkdir(parents=True)
    shutil.copy2(
        fixtures_dir / "mcp" / "fixture-xcatalog-mcp" / ".mcp.json",
        mcp_dir / ".mcp.json",
    )

    # Pre-existing plugin.json with different content
    plugin_dir = root / "plugins" / "fixture-xcatalog-mcp"
    plugin_dir.mkdir(parents=True)
    pre_existing = {"name": "fixture-xcatalog-mcp", "version": "0.0.1", "mcpServers": ".mcp.json"}
    plugin_json = plugin_dir / "plugin.json"
    plugin_json.write_text(json.dumps(pre_existing))

    config_dir = root / "system" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "marketplace.config.json").write_text(
        (fixtures_dir / "marketplace.config.json").read_text()
    )

    mod = _load("generate_marketplace")
    mod.build_marketplace(root)

    # plugin.json is unchanged
    assert json.loads(plugin_json.read_text()) == pre_existing


def test_build_marketplace_from_fixtures(fixtures_dir, tmp_path):
    root = tmp_path
    shutil.copytree(fixtures_dir / "plugins", root / "plugins")
    for newname in ["skills", "agents", "prompts", "mcp"]:
        src = fixtures_dir / newname
        if src.exists():
            shutil.copytree(src, root / newname)
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
                          "fixture-prompt", "fixture-skill", "fixture-xcatalog-mcp"}
    bundle = next(p for p in result["plugins"] if p["name"] == "fixture-bundle")
    assert bundle["source"] == "plugins/fixture-bundle"
    assert bundle["version"] == "1.0.0"
    assert bundle["skills"] == "skills"
    assert bundle["mcpServers"] == ".mcp.json"
    list_bundle = next(p for p in result["plugins"] if p["name"] == "fixture-list-bundle")
    assert list_bundle["source"] == "plugins/fixture-list-bundle/.copilot-plugin"
    assert list_bundle["skills"] == "skills"
    assert list_bundle["mcpServers"] == ".mcp.json"
    generated_plugin = root / "plugins" / "fixture-list-bundle" / ".copilot-plugin" / "plugin.json"
    generated_mcp = root / "plugins" / "fixture-list-bundle" / ".copilot-plugin" / ".mcp.json"
    assert generated_plugin.is_file()
    assert generated_mcp.is_file()
    assert json.loads(generated_mcp.read_text())["servers"] == {
        "fixture-top-server": {"command": "echo", "args": ["top"]}
    }
