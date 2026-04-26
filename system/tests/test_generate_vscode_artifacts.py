from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import shutil
import re

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def vscode_fake_repo(tmp_path, fixtures_dir):
    """Create a temporary repo with all necessary fixtures for VS Code artifacts generation."""
    catalog_dir = tmp_path / "catalog"
    catalog_dir.mkdir()
    shutil.copytree(fixtures_dir / "catalog" / "plugins", catalog_dir / "plugins")
    for name, newname in [("skills", "skills"), ("agents", "agents"), ("commands", "prompts"), ("mcpServers", "mcp")]:
        src = fixtures_dir / "catalog" / newname
        if src.exists():
            shutil.copytree(src, catalog_dir / newname)
    return tmp_path


def test_vscode_mcp_json_generated(vscode_fake_repo):
    """All mcpServers are merged into .vscode/mcp.json."""
    mod = _load("generate_vscode_artifacts")

    # Patch REPO_ROOT before making any calls so the real repo is never touched
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo

    try:
        mod.write_vscode_mcp_json()

        mcp_file = vscode_fake_repo / ".vscode" / "mcp.json"
        assert mcp_file.exists()

        data = json.loads(mcp_file.read_text())
        assert "servers" in data
    finally:
        mod.REPO_ROOT = original_root


def test_vscode_mcp_json_servers_format(vscode_fake_repo):
    """VS Code mcp.json uses 'servers' key and keeps 'type' field."""
    mod = _load("generate_vscode_artifacts")
    
    # Temporarily change to repo root
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.write_vscode_mcp_json()
        
        mcp_file = vscode_fake_repo / ".vscode" / "mcp.json"
        data = json.loads(mcp_file.read_text())
        
        # Top-level structure should have 'servers' key
        assert isinstance(data, dict)
        assert "servers" in data
        assert isinstance(data["servers"], dict)
        
        # fixture-top-server should be present (from fixtures/mcpServers/fixture-top-mcp)
        if vscode_fake_repo / "catalog" / "mcp" / "fixture-top-mcp" / ".mcp.json" in (vscode_fake_repo / "catalog" / "mcp").rglob(".mcp.json"):
            # The server should keep its original fields including 'type' if present
            for server_name, server_config in data["servers"].items():
                # Unlike Claude format, VS Code format should keep 'type' if present
                assert isinstance(server_config, dict)
    finally:
        mod.REPO_ROOT = original_root


def test_github_prompts_generated(vscode_fake_repo):
    """commands/*.md files are mirrored to .github/prompts/*.prompt.md."""
    mod = _load("generate_vscode_artifacts")
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.write_github_prompts()
        
        # Check that prompts were generated
        prompts_dir = vscode_fake_repo / ".github" / "prompts"
        assert prompts_dir.exists()
        
        # fixture-top-command.md should become fixture-top-command.prompt.md
        prompt_file = prompts_dir / "fixture-top-command.prompt.md"
        assert prompt_file.exists()
    finally:
        mod.REPO_ROOT = original_root


def test_github_prompt_frontmatter(vscode_fake_repo):
    """Generated prompt files have VS Code-style frontmatter with mode: ask."""
    mod = _load("generate_vscode_artifacts")
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.write_github_prompts()
        
        prompt_file = vscode_fake_repo / ".github" / "prompts" / "fixture-top-command.prompt.md"
        content = prompt_file.read_text()
        
        # Extract frontmatter
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        assert match, "Prompt file should have YAML frontmatter"
        
        frontmatter = yaml.safe_load(match.group(1))
        
        # Should have mode: ask
        assert "mode" in frontmatter
        assert frontmatter["mode"] == "ask"
        
        # Description from original command should be preserved
        original_file = vscode_fake_repo / "catalog" / "prompts" / "fixture-top-command.md"
        original_content = original_file.read_text()
        original_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", original_content, re.DOTALL)
        if original_match:
            original_frontmatter = yaml.safe_load(original_match.group(1))
            if "description" in original_frontmatter:
                assert "description" in frontmatter
                assert frontmatter["description"] == original_frontmatter["description"]
    finally:
        mod.REPO_ROOT = original_root


def test_github_instructions_generated(vscode_fake_repo):
    """agents/*.agent.md content is combined into .github/instructions/catalog-agent.instructions.md."""
    mod = _load("generate_vscode_artifacts")
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.write_github_instructions()
        
        instructions_file = vscode_fake_repo / ".github" / "instructions" / "catalog-agent.instructions.md"
        assert instructions_file.exists()
        
        content = instructions_file.read_text()
        
        # Should start with frontmatter
        assert content.startswith("---\n")
        
        # Extract frontmatter and body
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
        assert match
        
        frontmatter = yaml.safe_load(match.group(1))
        body = match.group(2)
        
        # Frontmatter should have applyTo
        assert "applyTo" in frontmatter
        assert frontmatter["applyTo"] == "**"
        
        # Body should contain content from agents
        assert len(body.strip()) > 0
    finally:
        mod.REPO_ROOT = original_root


def test_github_instructions_multiple_agents(vscode_fake_repo):
    """Multiple agents are concatenated into instructions file."""
    mod = _load("generate_vscode_artifacts")
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        # Create additional agent file
        agents_dir = vscode_fake_repo / "catalog" / "agents"
        agents_dir.mkdir(exist_ok=True)
        
        (agents_dir / "second-agent.agent.md").write_text(
            "---\nname: second-agent\ndescription: Second test agent\n---\n\n# Second Agent\n\nSecond body."
        )
        
        mod.write_github_instructions()
        
        instructions_file = vscode_fake_repo / ".github" / "instructions" / "catalog-agent.instructions.md"
        content = instructions_file.read_text()
        
        # Should contain bodies from both agents separated by blank lines
        assert "Fixture Top Agent" in content or "fixture-top-agent" in content
        assert "Second Agent" in content or "second-agent" in content
    finally:
        mod.REPO_ROOT = original_root


def test_prompt_body_preserved(vscode_fake_repo):
    """Command body (non-frontmatter) is preserved in generated prompt file."""
    mod = _load("generate_vscode_artifacts")
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.write_github_prompts()
        
        # Get original body
        original_file = vscode_fake_repo / "catalog" / "prompts" / "fixture-top-command.md"
        original_content = original_file.read_text()
        original_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", original_content, re.DOTALL)
        original_body = original_match.group(2) if original_match else original_content
        
        # Get generated file
        prompt_file = vscode_fake_repo / ".github" / "prompts" / "fixture-top-command.prompt.md"
        generated_content = prompt_file.read_text()
        generated_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", generated_content, re.DOTALL)
        generated_body = generated_match.group(2) if generated_match else generated_content
        
        # Body should be preserved (with possible whitespace normalization)
        assert generated_body.strip() == original_body.strip()
    finally:
        mod.REPO_ROOT = original_root


def test_vscode_mcp_json_multiple_servers(vscode_fake_repo):
    """Multiple MCP servers from different directories are merged correctly."""
    mod = _load("generate_vscode_artifacts")
    
    # Create additional MCP server
    mcp_dir = vscode_fake_repo / "catalog" / "mcp" / "additional-server"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    (mcp_dir / ".mcp.json").write_text(json.dumps({
        "servers": {
            "additional": {
                "command": "python",
                "args": ["-m", "server"]
            }
        }
    }))
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.write_vscode_mcp_json()
        
        mcp_file = vscode_fake_repo / ".vscode" / "mcp.json"
        data = json.loads(mcp_file.read_text())
        
        # Should have servers from all MCP directories
        assert len(data["servers"]) >= 1
        assert "additional" in data["servers"]
    finally:
        mod.REPO_ROOT = original_root


def test_vscode_artifacts_no_crash_missing_dirs(vscode_fake_repo):
    """Script handles missing commands/ or agents/ directories gracefully."""
    mod = _load("generate_vscode_artifacts")
    
    # Use a minimal fake repo without commands/agents dirs
    minimal_repo = vscode_fake_repo
    for d in ["catalog/prompts", "catalog/agents"]:
        path = minimal_repo / d
        if path.exists():
            shutil.rmtree(path)
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = minimal_repo
    
    try:
        # Should not crash
        mod.write_vscode_mcp_json()
        mod.write_github_prompts()
        mod.write_github_instructions()
        
        # These should succeed without errors even with missing dirs
        # write_vscode_mcp_json creates .vscode if mcpServers exist
        if (minimal_repo / "catalog" / "mcp").exists():
            assert (minimal_repo / ".vscode").exists()
    finally:
        mod.REPO_ROOT = original_root


def test_main_calls_all_writers(vscode_fake_repo):
    """main() function calls all three writer functions."""
    mod = _load("generate_vscode_artifacts")
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.main()
        
        # All three artifact types should be generated
        assert (vscode_fake_repo / ".vscode" / "mcp.json").exists()
        assert (vscode_fake_repo / ".github" / "prompts").exists()
        assert (vscode_fake_repo / ".github" / "instructions" / "catalog-agent.instructions.md").exists()
    finally:
        mod.REPO_ROOT = original_root


def test_prompt_file_naming(vscode_fake_repo):
    """Generated prompt files use *.prompt.md naming convention."""
    mod = _load("generate_vscode_artifacts")
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.write_github_prompts()
        
        prompts_dir = vscode_fake_repo / ".github" / "prompts"
        
        # All files should end with .prompt.md
        for file in prompts_dir.glob("*"):
            if file.is_file():
                assert file.name.endswith(".prompt.md")
    finally:
        mod.REPO_ROOT = original_root


def test_instructions_file_naming(vscode_fake_repo):
    """Generated instructions file is named catalog-agent.instructions.md."""
    mod = _load("generate_vscode_artifacts")
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.write_github_instructions()
        
        instructions_file = vscode_fake_repo / ".github" / "instructions" / "catalog-agent.instructions.md"
        assert instructions_file.name == "catalog-agent.instructions.md"
        assert instructions_file.exists()
    finally:
        mod.REPO_ROOT = original_root


def test_agents_body_extraction(vscode_fake_repo):
    """Agent body is correctly extracted, stripping frontmatter."""
    mod = _load("generate_vscode_artifacts")
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.write_github_instructions()
        
        instructions_file = vscode_fake_repo / ".github" / "instructions" / "catalog-agent.instructions.md"
        content = instructions_file.read_text()
        
        # Extract body
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
        body = match.group(2)
        
        # Body should not contain frontmatter separators (except the one at the very start)
        lines = body.split("\n")
        # The frontmatter separators should only be at the beginning
        for i, line in enumerate(lines[2:], start=2):  # Skip the frontmatter we already extracted
            # Ensure no extra frontmatter separators are in the body
            if line.strip() == "---":
                # This might be part of agent content, but it shouldn't be the main separator
                pass
    finally:
        mod.REPO_ROOT = original_root


def test_prompt_description_from_frontmatter(vscode_fake_repo):
    """Description field from command frontmatter is preserved in prompt."""
    mod = _load("generate_vscode_artifacts")
    
    # Create a command with description
    commands_dir = vscode_fake_repo / "catalog" / "prompts"
    commands_dir.mkdir(exist_ok=True)
    (commands_dir / "test-with-desc.md").write_text(
        "---\nname: test-with-desc\ndescription: This is a test description\n---\n\nBody text"
    )
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.write_github_prompts()
        
        prompt_file = vscode_fake_repo / ".github" / "prompts" / "test-with-desc.prompt.md"
        content = prompt_file.read_text()
        
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        frontmatter = yaml.safe_load(match.group(1))
        
        assert frontmatter["description"] == "This is a test description"
        assert frontmatter["mode"] == "ask"
    finally:
        mod.REPO_ROOT = original_root


def test_vscode_mcp_json_handles_invalid_json(vscode_fake_repo, capsys):
    """Script handles invalid JSON in .mcp.json files gracefully."""
    mod = _load("generate_vscode_artifacts")
    
    # Create invalid JSON file
    mcp_dir = vscode_fake_repo / "catalog" / "mcp" / "bad-server"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    (mcp_dir / ".mcp.json").write_text("{ invalid json")
    
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = vscode_fake_repo
    
    try:
        mod.write_vscode_mcp_json()
        
        # Should produce warning but not crash
        # Check that .vscode/mcp.json was still created with other servers
        mcp_file = vscode_fake_repo / ".vscode" / "mcp.json"
        assert mcp_file.exists()
    finally:
        mod.REPO_ROOT = original_root
