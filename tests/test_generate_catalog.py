from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def fake_repo(tmp_path, fixtures_dir):
    (tmp_path / "plugins").symlink_to(fixtures_dir / "plugins")
    (tmp_path / "templates").symlink_to(fixtures_dir / "templates")
    return tmp_path


def test_catalog_types(fake_repo):
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    types = {p["name"]: p["type"] for p in catalog["plugins"]}
    assert types["fixture-skill"] == "skill"
    assert types["fixture-mcp"] == "mcp"
    assert types["fixture-agent"] == "agent"
    assert types["fixture-prompt"] == "prompt"
    assert types["fixture-bundle"] == "bundle"


def test_catalog_components(fake_repo):
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    bundle = next(p for p in catalog["plugins"] if p["name"] == "fixture-bundle")
    assert bundle["components"]["skills"] == ["fixture-skill"]
    assert bundle["components"]["mcpServers"] == ["bundle-server"]
    assert bundle["components"]["agents"] == []
    assert bundle["components"]["commands"] == []


def test_catalog_install_fields(fake_repo):
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    mcp = next(p for p in catalog["plugins"] if p["name"] == "fixture-mcp")
    assert mcp["install"]["copilot"] == "fixture-mcp@ai-catalog"
    assert mcp["install"]["zip"] == "dl/fixture-mcp.zip"
    assert mcp["install"]["repoPath"] == "plugins/fixture-mcp"
    assert mcp["install"]["vscodeMcpDeeplink"].startswith("vscode:mcp/install?name=fixture-server&config=")
    skill = next(p for p in catalog["plugins"] if p["name"] == "fixture-skill")
    assert skill["install"]["vscodeMcpDeeplink"] is None
    assert skill["install"]["rawFiles"] == ["skills/fixture-skill/SKILL.md"]


def test_catalog_templates(fake_repo):
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    assert len(catalog["templates"]) == 1
    tpl = catalog["templates"][0]
    assert tpl["name"] == "fixture-template"
    assert tpl["type"] == "template"
    assert tpl["install"]["rawFiles"] == ["TEMPLATE.md"]
    assert tpl["install"]["zip"] == "dl/fixture-template.zip"
    assert "copilot" not in tpl["install"]


def test_catalog_deeplink_size_cap(tmp_path, fixtures_dir):
    mod = _load("generate_catalog")
    # Build a synthetic repo: copy fixtures then add an oversized MCP plugin
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    import shutil
    for p in (fixtures_dir / "plugins").iterdir():
        shutil.copytree(p, plugins_root / p.name)
    big_plugin = plugins_root / "fixture-giant-mcp"
    big_plugin.mkdir()
    (big_plugin / "plugin.json").write_text(json.dumps({
        "name": "fixture-giant-mcp", "version": "1.0.0", "mcpServers": ".mcp.json",
    }))
    huge_args = ["x" * 3000]
    (big_plugin / ".mcp.json").write_text(json.dumps({"servers": {"big": {"command": "echo", "args": huge_args}}}))
    (tmp_path / "templates").mkdir()
    catalog = mod.build_catalog(tmp_path)
    big = next(p for p in catalog["plugins"] if p["name"] == "fixture-giant-mcp")
    assert big["install"]["vscodeMcpDeeplink"] is None, "deeplink must be None when >2KB"
