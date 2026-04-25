from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def claude_fake_repo(tmp_path, fixtures_dir):
    """Create a temporary repo with all necessary fixtures for Claude marketplace generation."""
    shutil.copytree(fixtures_dir / "plugins", tmp_path / "plugins")
    for name in ("skills", "agents", "commands", "mcpServers"):
        src = fixtures_dir / name
        if src.exists():
            shutil.copytree(src, tmp_path / name)
    (tmp_path / "marketplace.config.json").write_text(
        (fixtures_dir / "marketplace.config.json").read_text()
    )
    return tmp_path


def test_mcp_transform_drops_type(claude_fake_repo):
    """MCP servers in Claude plugin manifest must not have 'type' field."""
    mod = _load("generate_claude_marketplace")
    
    # Create a test plugin with inline MCP that includes a 'type' field
    plugin_dir = claude_fake_repo / "plugins" / "test-mcp-type"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.json").write_text(json.dumps({
        "name": "test-mcp-type",
        "description": "Test MCP type dropping",
        "version": "1.0.0",
        "mcpServers": ".mcp.json",
    }))
    (plugin_dir / ".mcp.json").write_text(json.dumps({
        "servers": {
            "test-server": {
                "command": "echo",
                "args": ["hello"],
                "type": "stdio",  # This should be dropped
            }
        }
    }))
    
    marketplace = mod.build_claude_marketplace(claude_fake_repo)
    
    # Find the generated claude-plugin.json
    claude_manifest = json.loads((plugin_dir / "claude-plugin.json").read_text())
    
    # MCP servers should not have 'type' field
    assert "mcpServers" in claude_manifest
    assert "test-server" in claude_manifest["mcpServers"]
    server_config = claude_manifest["mcpServers"]["test-server"]
    assert "type" not in server_config
    assert server_config["command"] == "echo"
    assert server_config["args"] == ["hello"]


def test_claude_plugin_json_generated(claude_fake_repo):
    """Each plugin dir gets a claude-plugin.json file."""
    mod = _load("generate_claude_marketplace")
    mod.build_claude_marketplace(claude_fake_repo)
    
    plugins_dir = claude_fake_repo / "plugins"
    generated_files = []
    for plugin_dir in plugins_dir.iterdir():
        if plugin_dir.is_dir() and (plugin_dir / "claude-plugin.json").exists():
            generated_files.append(plugin_dir.name)
    
    # Should have claude-plugin.json for all fixture plugins
    assert len(generated_files) > 0
    assert "fixture-mcp" in generated_files
    assert "fixture-prompt" in generated_files


def test_claude_marketplace_json_generated(claude_fake_repo):
    """claude.marketplace.json is generated at repo root with correct structure."""
    mod = _load("generate_claude_marketplace")
    
    # Patch REPO_ROOT to use our fake repo
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = claude_fake_repo
    
    try:
        # main() writes the file; build_claude_marketplace() just returns the structure
        mod.main()
        
        marketplace_file = claude_fake_repo / "claude.marketplace.json"
        assert marketplace_file.exists()
        
        marketplace = json.loads(marketplace_file.read_text())
        
        # Check top-level structure
        assert "name" in marketplace
        assert "version" in marketplace
        assert "description" in marketplace
        assert "plugins" in marketplace
        assert isinstance(marketplace["plugins"], list)
        
        # Should have plugins
        assert len(marketplace["plugins"]) > 0
    finally:
        mod.REPO_ROOT = original_root


def test_claude_marketplace_source_url(claude_fake_repo):
    """Source URL in marketplace comes from marketplace.config.json owner/name."""
    mod = _load("generate_claude_marketplace")
    marketplace = mod.build_claude_marketplace(claude_fake_repo)
    
    # All plugins should have correct source URL from marketplace config
    for plugin in marketplace["plugins"]:
        assert "source" in plugin
        assert plugin["source"]["type"] == "git"
        assert "https://github.com/fixture-owner/" in plugin["source"]["url"]
        assert plugin["source"]["url"].endswith("fixture-marketplace")


def test_list_reference_mcp_resolved(claude_fake_repo):
    """List-reference mcpServers (e.g. ['fixture-top-mcp']) are resolved from mcpServers/ dir."""
    mod = _load("generate_claude_marketplace")
    mod.build_claude_marketplace(claude_fake_repo)
    
    # fixture-list-bundle has mcpServers: ["fixture-top-mcp"]
    plugin_dir = claude_fake_repo / "plugins" / "fixture-list-bundle"
    claude_manifest = json.loads((plugin_dir / "claude-plugin.json").read_text())
    
    # Should have resolved MCP servers
    assert "mcpServers" in claude_manifest
    assert "fixture-top-server" in claude_manifest["mcpServers"]
    assert claude_manifest["mcpServers"]["fixture-top-server"]["command"] == "echo"
    assert claude_manifest["mcpServers"]["fixture-top-server"]["args"] == ["top"]


def test_claude_plugin_with_commands(claude_fake_repo):
    """Commands are resolved and included in slashCommands field."""
    mod = _load("generate_claude_marketplace")
    mod.build_claude_marketplace(claude_fake_repo)
    
    # fixture-prompt has commands
    plugin_dir = claude_fake_repo / "plugins" / "fixture-prompt"
    claude_manifest = json.loads((plugin_dir / "claude-plugin.json").read_text())
    
    assert "slashCommands" in claude_manifest
    assert isinstance(claude_manifest["slashCommands"], list)
    assert len(claude_manifest["slashCommands"]) > 0
    
    cmd = claude_manifest["slashCommands"][0]
    assert "name" in cmd
    assert "description" in cmd
    assert "prompt" in cmd
    assert cmd["prompt"] == "commands/fixture-prompt.md"


def test_claude_plugin_with_agents(claude_fake_repo):
    """Agents are resolved and included in instructions field."""
    mod = _load("generate_claude_marketplace")
    mod.build_claude_marketplace(claude_fake_repo)
    
    # fixture-agent has agents
    plugin_dir = claude_fake_repo / "plugins" / "fixture-agent"
    claude_manifest = json.loads((plugin_dir / "claude-plugin.json").read_text())
    
    assert "instructions" in claude_manifest
    # Single agent becomes string, multiple agents become list
    assert isinstance(claude_manifest["instructions"], str)
    assert claude_manifest["instructions"] == "agents/fixture-agent.agent.md"


def test_claude_plugin_passthrough_fields(claude_fake_repo):
    """Passthrough fields are included in generated claude-plugin.json."""
    mod = _load("generate_claude_marketplace")
    mod.build_claude_marketplace(claude_fake_repo)
    
    plugin_dir = claude_fake_repo / "plugins" / "fixture-mcp"
    claude_manifest = json.loads((plugin_dir / "claude-plugin.json").read_text())
    
    # Check that passthrough fields are present
    assert claude_manifest["name"] == "fixture-mcp"
    assert claude_manifest["description"] == "A fixture MCP plugin."
    assert claude_manifest["version"] == "1.0.0"
    assert "keywords" in claude_manifest
    assert "category" in claude_manifest


def test_claude_marketplace_plugin_entries(claude_fake_repo):
    """Marketplace entries have correct structure with git source and manifest path."""
    mod = _load("generate_claude_marketplace")
    marketplace = mod.build_claude_marketplace(claude_fake_repo)
    
    entry = marketplace["plugins"][0]
    
    # Check entry structure
    assert "name" in entry
    assert "source" in entry
    assert "manifest" in entry
    
    # Source should have git type
    source = entry["source"]
    assert source["type"] == "git"
    assert "path" in source
    assert source["path"].startswith("plugins/")
    
    # Manifest file should be specified
    assert entry["manifest"] == "claude-plugin.json"


def test_claude_plugin_materialized_directory(claude_fake_repo):
    """Each plugin gets a .claude-plugin directory with materialized files."""
    mod = _load("generate_claude_marketplace")
    mod.build_claude_marketplace(claude_fake_repo)
    
    # fixture-prompt should have .claude-plugin with commands
    plugin_dir = claude_fake_repo / "plugins" / "fixture-prompt"
    claude_plugin_dir = plugin_dir / ".claude-plugin"
    
    assert claude_plugin_dir.exists()
    assert (claude_plugin_dir / "claude-plugin.json").exists()
    
    # If commands exist, should be materialized
    if (plugin_dir / "commands").exists():
        assert (claude_plugin_dir / "commands").exists()


def test_inline_mcp_servers_transformed(claude_fake_repo):
    """Inline MCP servers (string path) are loaded and transformed correctly."""
    mod = _load("generate_claude_marketplace")
    mod.build_claude_marketplace(claude_fake_repo)
    
    # fixture-mcp uses inline .mcp.json
    plugin_dir = claude_fake_repo / "plugins" / "fixture-mcp"
    claude_manifest = json.loads((plugin_dir / "claude-plugin.json").read_text())
    
    assert "mcpServers" in claude_manifest
    assert "fixture-server" in claude_manifest["mcpServers"]
    # Verify type field is not present
    assert "type" not in claude_manifest["mcpServers"]["fixture-server"]


def test_list_reference_commands_from_topLevel(claude_fake_repo):
    """List-reference commands are resolved from repo root commands/ directory."""
    mod = _load("generate_claude_marketplace")
    
    # Create a test plugin with list-reference commands
    plugin_dir = claude_fake_repo / "plugins" / "test-list-cmd"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.json").write_text(json.dumps({
        "name": "test-list-cmd",
        "description": "Test list ref commands",
        "version": "1.0.0",
        "commands": ["fixture-top-command"],  # List reference
    }))
    
    mod.build_claude_marketplace(claude_fake_repo)
    
    claude_manifest = json.loads((plugin_dir / "claude-plugin.json").read_text())
    
    assert "slashCommands" in claude_manifest
    assert len(claude_manifest["slashCommands"]) == 1
    assert claude_manifest["slashCommands"][0]["name"] == "fixture-top-command"


def test_list_reference_agents_from_topLevel(claude_fake_repo):
    """List-reference agents are resolved from repo root agents/ directory."""
    mod = _load("generate_claude_marketplace")
    
    # Create a test plugin with list-reference agents
    plugin_dir = claude_fake_repo / "plugins" / "test-list-agent"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.json").write_text(json.dumps({
        "name": "test-list-agent",
        "description": "Test list ref agents",
        "version": "1.0.0",
        "agents": ["fixture-top-agent"],  # List reference
    }))
    
    mod.build_claude_marketplace(claude_fake_repo)
    
    claude_manifest = json.loads((plugin_dir / "claude-plugin.json").read_text())
    
    assert "instructions" in claude_manifest
    assert claude_manifest["instructions"] == "agents/fixture-top-agent.agent.md"
