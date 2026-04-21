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
    (tmp_path / "marketplace.config.json").write_text(
        (fixtures_dir / "marketplace.config.json").read_text()
    )
    scripts_link = tmp_path / "scripts"
    scripts_link.symlink_to(SCRIPTS)
    for name in ("skills", "agents", "commands", "mcpServers"):
        src = fixtures_dir / name
        if src.exists():
            (tmp_path / name).symlink_to(src)
    return tmp_path


def test_fixtures_pass_validation(fake_repo):
    mod = _load("validate_catalog")
    v = mod.Validator(fake_repo)
    exit_code = v.run()
    assert v.errors == [], f"unexpected errors: {v.errors}"
    assert exit_code == 0


def test_bad_name_fails(tmp_path, fixtures_dir):
    mod = _load("validate_catalog")
    (tmp_path / "plugins").mkdir()
    (tmp_path / "templates").symlink_to(fixtures_dir / "templates")
    (tmp_path / "scripts").symlink_to(SCRIPTS)
    bad = tmp_path / "plugins" / "bad-name"
    bad.mkdir()
    (bad / "plugin.json").write_text(json.dumps({"name": "Bad_Name"}))
    v = mod.Validator(tmp_path)
    v.run()
    assert any("Bad_Name" in e or "kebab" in e.lower() or "pattern" in e.lower() for e in v.errors)


def test_duplicate_mcp_server_fails(fake_repo):
    mod = _load("validate_catalog")
    plugins = fake_repo / "plugins"
    # symlink has fixtures mode; copy to a writable dir
    import shutil
    real_plugins = fake_repo / "plugins_real"
    real_plugins.mkdir()
    for p in plugins.iterdir():
        shutil.copytree(p, real_plugins / p.name)
    plugins.unlink()
    real_plugins.rename(fake_repo / "plugins")
    dup = fake_repo / "plugins" / "fixture-dup-mcp"
    dup.mkdir()
    (dup / "plugin.json").write_text(json.dumps({"name": "fixture-dup-mcp", "mcpServers": ".mcp.json"}))
    (dup / ".mcp.json").write_text(json.dumps({"servers": {"fixture-server": {"command": "echo"}}}))
    v = mod.Validator(fake_repo)
    v.run()
    assert any("fixture-server" in e for e in v.errors)


def test_secret_scan_fails(tmp_path, fixtures_dir):
    mod = _load("validate_catalog")
    (tmp_path / "plugins").mkdir()
    (tmp_path / "templates").symlink_to(fixtures_dir / "templates")
    (tmp_path / "scripts").symlink_to(SCRIPTS)
    leaky = tmp_path / "plugins" / "fixture-leaky"
    leaky.mkdir()
    (leaky / "plugin.json").write_text(json.dumps({"name": "fixture-leaky", "mcpServers": ".mcp.json"}))
    (leaky / ".mcp.json").write_text(json.dumps({
        "servers": {"leaky": {"command": "echo", "env": {"API_TOKEN": "ghp_" + "a" * 36}}}
    }))
    v = mod.Validator(tmp_path)
    v.run()
    assert any("secret" in e.lower() or "ghp_" in e for e in v.errors)


def test_frontmatter_drift_is_warning_not_error(tmp_path, fixtures_dir):
    mod = _load("validate_catalog")
    (tmp_path / "plugins").mkdir()
    (tmp_path / "templates").symlink_to(fixtures_dir / "templates")
    (tmp_path / "scripts").symlink_to(SCRIPTS)
    drifted = tmp_path / "plugins" / "fixture-drift"
    drifted.mkdir()
    (drifted / "plugin.json").write_text(json.dumps({
        "name": "fixture-drift", "version": "2.0.0", "skills": "skills"
    }))
    skill_dir = drifted / "skills" / "fixture-drift"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: fixture-drift\nversion: 1.0.0\n---\nbody")
    v = mod.Validator(tmp_path)
    exit_code = v.run()
    assert any("drifts" in w for w in v.warnings)
    assert exit_code == 0, "drift must be a warning, not an error"


def test_fixtures_pass_validation_with_top_level_dirs(fake_repo):
    mod = _load("validate_catalog")
    v = mod.Validator(fake_repo)
    exit_code = v.run()
    assert v.errors == [], f"unexpected errors: {v.errors}"
    assert exit_code == 0


def test_list_ref_missing_skill_fails(tmp_path, fixtures_dir):
    mod = _load("validate_catalog")
    (tmp_path / "plugins").mkdir()
    (tmp_path / "templates").symlink_to(fixtures_dir / "templates")
    (tmp_path / "scripts").symlink_to(SCRIPTS)
    bad = tmp_path / "plugins" / "fixture-bad-ref"
    bad.mkdir()
    (bad / "plugin.json").write_text(json.dumps({
        "name": "fixture-bad-ref",
        "skills": ["nonexistent-skill"],
    }))
    v = mod.Validator(tmp_path)
    v.run()
    assert any("nonexistent-skill" in e for e in v.errors)


def test_list_ref_missing_agent_fails(tmp_path, fixtures_dir):
    mod = _load("validate_catalog")
    (tmp_path / "plugins").mkdir()
    (tmp_path / "templates").symlink_to(fixtures_dir / "templates")
    (tmp_path / "scripts").symlink_to(SCRIPTS)
    bad = tmp_path / "plugins" / "fixture-bad-agent-ref"
    bad.mkdir()
    (bad / "plugin.json").write_text(json.dumps({
        "name": "fixture-bad-agent-ref",
        "agents": ["ghost-agent"],
    }))
    v = mod.Validator(tmp_path)
    v.run()
    assert any("ghost-agent" in e for e in v.errors)


def test_list_ref_missing_command_fails(tmp_path, fixtures_dir):
    mod = _load("validate_catalog")
    (tmp_path / "plugins").mkdir()
    (tmp_path / "templates").symlink_to(fixtures_dir / "templates")
    (tmp_path / "scripts").symlink_to(SCRIPTS)
    bad = tmp_path / "plugins" / "fixture-bad-cmd-ref"
    bad.mkdir()
    (bad / "plugin.json").write_text(json.dumps({
        "name": "fixture-bad-cmd-ref",
        "commands": ["ghost-cmd"],
    }))
    v = mod.Validator(tmp_path)
    v.run()
    assert any("ghost-cmd" in e for e in v.errors)


def test_list_ref_missing_mcp_fails(tmp_path, fixtures_dir):
    mod = _load("validate_catalog")
    (tmp_path / "plugins").mkdir()
    (tmp_path / "templates").symlink_to(fixtures_dir / "templates")
    (tmp_path / "scripts").symlink_to(SCRIPTS)
    bad = tmp_path / "plugins" / "fixture-bad-mcp-ref"
    bad.mkdir()
    (bad / "plugin.json").write_text(json.dumps({
        "name": "fixture-bad-mcp-ref",
        "mcpServers": ["ghost-mcp"],
    }))
    v = mod.Validator(tmp_path)
    v.run()
    assert any("ghost-mcp" in e for e in v.errors)


def test_standalone_skill_missing_description_fails(tmp_path, fixtures_dir):
    mod = _load("validate_catalog")
    (tmp_path / "plugins").mkdir()
    (tmp_path / "templates").symlink_to(fixtures_dir / "templates")
    (tmp_path / "scripts").symlink_to(SCRIPTS)
    skills_dir = tmp_path / "skills" / "no-desc-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("---\nname: no-desc-skill\n---\nbody")
    v = mod.Validator(tmp_path)
    v.run()
    assert any("description" in e for e in v.errors)


def test_standalone_mcp_secret_scan_fails(tmp_path, fixtures_dir):
    mod = _load("validate_catalog")
    (tmp_path / "plugins").mkdir()
    (tmp_path / "templates").symlink_to(fixtures_dir / "templates")
    (tmp_path / "scripts").symlink_to(SCRIPTS)
    mcp_dir = tmp_path / "mcpServers" / "leaky-top-mcp"
    mcp_dir.mkdir(parents=True)
    (mcp_dir / ".mcp.json").write_text(json.dumps({
        "servers": {"leaky": {"command": "echo", "env": {"API_TOKEN": "ghp_" + "a" * 36}}}
    }))
    v = mod.Validator(tmp_path)
    v.run()
    assert any("secret" in e.lower() or "ghp_" in e for e in v.errors)
