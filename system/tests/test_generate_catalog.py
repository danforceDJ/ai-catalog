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
    for newname in ["skills", "agents", "prompts", "mcp"]:
        src = fixtures_dir / newname
        if src.exists():
            (tmp_path / newname).symlink_to(src)
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
    assert types["fixture-list-bundle"] == "bundle"


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
    assert mcp["install"]["vscodeMcpDeeplink"].startswith("vscode:mcp/install?%7B%22name%22%3A%22fixture-server%22")
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
    for newname in ["skills", "agents", "prompts", "mcp"]:
        src = fixtures_dir / newname
        if src.exists():
            (tmp_path / newname).symlink_to(src)
    catalog = mod.build_catalog(tmp_path)
    big = next(p for p in catalog["plugins"] if p["name"] == "fixture-giant-mcp")
    assert big["install"]["vscodeMcpDeeplink"] is None, "deeplink must be None when >2KB"


def test_catalog_list_ref_bundle_components(fake_repo):
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    bundle = next(p for p in catalog["plugins"] if p["name"] == "fixture-list-bundle")
    assert bundle["type"] == "bundle"
    assert bundle["components"]["skills"] == ["fixture-top-skill"]
    assert bundle["components"]["mcpServers"] == ["fixture-top-server"]
    assert bundle["components"]["agents"] == []
    assert bundle["components"]["commands"] == []


def test_catalog_list_ref_bundle_raw_files_empty(fake_repo):
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    bundle = next(p for p in catalog["plugins"] if p["name"] == "fixture-list-bundle")
    # Wrapper plugins using list refs have no raw files; standalone entries carry them
    assert bundle["install"]["rawFiles"] == []


def test_catalog_list_ref_bundle_deeplink(fake_repo):
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    bundle = next(p for p in catalog["plugins"] if p["name"] == "fixture-list-bundle")
    # Single top-level MCP reference → deeplink generated
    assert bundle["install"]["vscodeMcpDeeplink"] is not None
    assert bundle["install"]["vscodeMcpDeeplink"].startswith("vscode:mcp/install?%7B%22name%22%3A%22fixture-top-server%22")


def test_catalog_standalone_entries_for_uncovered_primitives(fake_repo):
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    names = {p["name"] for p in catalog["plugins"]}
    # fixture-top-skill is covered by fixture-list-bundle → no standalone entry
    assert "fixture-top-skill" not in names
    # fixture-top-mcp is covered by fixture-list-bundle → no standalone entry
    assert "fixture-top-mcp" not in names
    # fixture-top-agent/command are NOT referenced by any plugin → standalone entries appear
    assert "fixture-top-agent" in names
    assert "fixture-top-command" in names


def test_catalog_standalone_agent_install(fake_repo):
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    agent = next(p for p in catalog["plugins"] if p["name"] == "fixture-top-agent")
    assert agent["type"] == "agent"
    assert agent["install"]["copilot"] is None
    assert agent["install"]["rawFiles"] == ["fixture-top-agent.agent.md"]
    assert agent["install"]["repoPath"] == "agents"


def test_catalog_standalone_command_install(fake_repo):
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    cmd = next(p for p in catalog["plugins"] if p["name"] == "fixture-top-command")
    assert cmd["type"] == "prompt"
    assert cmd["install"]["copilot"] is None
    assert cmd["install"]["rawFiles"] == ["fixture-top-command.md"]


def test_catalog_standalone_mcp_xcatalog_fields(fake_repo):
    """Standalone MCP .mcp.json with x-catalog block → catalog entry carries all metadata fields."""
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    entry = next((p for p in catalog["plugins"] if p["name"] == "fixture-xcatalog-mcp"), None)
    assert entry is not None, "fixture-xcatalog-mcp should appear as a standalone entry"
    assert entry["type"] == "mcp"
    assert entry["description"] == "A fixture MCP server with x-catalog metadata."
    assert entry["version"] == "2.3.4"
    assert entry["category"] == "testing"
    assert entry["tags"] == ["fixture", "xcatalog"]
    assert entry["keywords"] == ["test", "metadata"]
    assert entry["components"]["mcpServers"] == ["fixture-xcatalog-server"]
    assert entry["install"]["repoPath"] == "mcp/fixture-xcatalog-mcp"
    assert entry["install"]["zip"] == "dl/fixture-xcatalog-mcp.zip"
    assert entry["install"]["copilot"] is None


def test_catalog_standalone_mcp_no_xcatalog_defaults(fake_repo):
    """Standalone MCP .mcp.json without x-catalog block → catalog entry uses empty defaults."""
    mod = _load("generate_catalog")
    catalog = mod.build_catalog(fake_repo)
    entry = next((p for p in catalog["plugins"] if p["name"] == "fixture-no-xcatalog-mcp"), None)
    assert entry is not None, "fixture-no-xcatalog-mcp should appear as a standalone entry"
    assert entry["type"] == "mcp"
    assert entry["description"] == ""
    assert entry["version"] == ""
    assert entry["category"] == ""
    assert entry["tags"] == []
    assert entry["keywords"] == []
    assert entry["components"]["mcpServers"] == ["fixture-no-xcatalog-server"]


def test_catalog_missing_top_level_ref_resolves_gracefully(tmp_path, fixtures_dir):
    mod = _load("generate_catalog")
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    bad = plugins_root / "fixture-bad-ref"
    bad.mkdir()
    (bad / "plugin.json").write_text(json.dumps({
        "name": "fixture-bad-ref",
        "skills": ["nonexistent-skill"],
    }))
    (tmp_path / "templates").mkdir()
    catalog = mod.build_catalog(tmp_path)
    entry = next(p for p in catalog["plugins"] if p["name"] == "fixture-bad-ref")
    # Missing referenced skill → resolved as empty list, entry still generated
    assert entry["components"]["skills"] == []
    assert entry["type"] == "empty"
