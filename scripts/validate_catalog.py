#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "jsonschema>=4"]
# ///
"""Validate the catalog structure. Exits 1 on invariant violation."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from typing import Any
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|api[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"gho_[A-Za-z0-9]{36}"),
    re.compile(r"ghu_[A-Za-z0-9]{36}"),
    re.compile(r"\"API_TOKEN\"\s*:\s*\"[^\"]{8,}\""),
]


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def _first(value: Any, default: str) -> str:
    if isinstance(value, list):
        return value[0] if value else default
    if isinstance(value, str):
        return value
    return default


class Validator:
    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.errors: list[str] = []
        self.warnings: list[str] = []
        schema_dir = repo / "scripts" / "schemas"
        if not schema_dir.is_dir():
            schema_dir = SCHEMA_DIR
        self.plugin_validator = Draft202012Validator(
            json.loads((schema_dir / "plugin.schema.json").read_text())
        )
        self.marketplace_validator = Draft202012Validator(
            json.loads((schema_dir / "marketplace.schema.json").read_text())
        )

    def fail(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def check_kebab(self, name: str, context: str) -> None:
        if not KEBAB_RE.match(name or "") or len(name) > 64:
            self.fail(f"{context}: name '{name}' is not kebab-case or exceeds 64 chars")

    def validate_plugin(self, plugin_dir: Path) -> None:
        manifest_path = plugin_dir / "plugin.json"
        if not manifest_path.is_file():
            self.fail(f"{plugin_dir.relative_to(self.repo)}: missing plugin.json")
            return
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError as exc:
            self.fail(f"{manifest_path}: invalid JSON: {exc}")
            return
        for err in sorted(self.plugin_validator.iter_errors(manifest), key=lambda e: list(e.path)):
            self.fail(f"{manifest_path}: schema: {err.message}")
        name = manifest.get("name", "")
        self.check_kebab(name, str(manifest_path))
        if name and name != plugin_dir.name:
            self.fail(f"{manifest_path}: name '{name}' != directory '{plugin_dir.name}'")
        self._check_components(plugin_dir, manifest)
        self._check_frontmatter_drift(plugin_dir, manifest)
        self._scan_secrets(plugin_dir, manifest)

    def _check_components(self, plugin_dir: Path, manifest: dict) -> None:
        skills_path = plugin_dir / _first(manifest.get("skills", "skills"), "skills")
        if "skills" in manifest or skills_path.is_dir():
            if not skills_path.is_dir():
                self.fail(f"{plugin_dir}: skills dir '{skills_path.name}' not found")
            elif not any((s / "SKILL.md").is_file() for s in skills_path.iterdir() if s.is_dir()):
                self.fail(f"{skills_path}: no SKILL.md found in any subdirectory")
        agents_path = plugin_dir / _first(manifest.get("agents", "agents"), "agents")
        if "agents" in manifest or agents_path.is_dir():
            if not agents_path.is_dir():
                self.fail(f"{plugin_dir}: agents dir not found")
            elif not list(agents_path.glob("*.agent.md")):
                self.fail(f"{agents_path}: no *.agent.md files")
        commands_path = plugin_dir / _first(manifest.get("commands", "commands"), "commands")
        if "commands" in manifest or commands_path.is_dir():
            if not commands_path.is_dir():
                self.fail(f"{plugin_dir}: commands dir not found")
            else:
                for cmd in commands_path.glob("*.md"):
                    fm = parse_frontmatter(cmd.read_text())
                    if not fm.get("name") or not fm.get("description"):
                        self.fail(f"{cmd}: missing name/description frontmatter")
                    if fm.get("name") and fm["name"] != cmd.stem:
                        self.fail(f"{cmd}: frontmatter name '{fm['name']}' != filename '{cmd.stem}'")

    def _check_frontmatter_drift(self, plugin_dir: Path, manifest: dict) -> None:
        skills_path = plugin_dir / _first(manifest.get("skills", "skills"), "skills")
        if not skills_path.is_dir():
            return
        for s in skills_path.iterdir():
            skill_md = s / "SKILL.md"
            if not skill_md.is_file():
                continue
            fm = parse_frontmatter(skill_md.read_text())
            for key in ("version",):
                if key in fm and key in manifest and fm[key] != manifest[key]:
                    self.warn(f"{skill_md}: frontmatter {key}='{fm[key]}' drifts from plugin.json '{manifest[key]}'")

    def _scan_secrets(self, plugin_dir: Path, manifest: dict) -> None:
        mcp_value = manifest.get("mcpServers", ".mcp.json")
        if not isinstance(mcp_value, str):
            return
        mcp_path = plugin_dir / mcp_value
        if not mcp_path.is_file():
            return
        text = mcp_path.read_text()
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                self.fail(f"{mcp_path}: possible secret matching pattern {pat.pattern!r}")
                return

    def check_global_uniqueness(self, plugin_dirs: list[Path]) -> None:
        names: dict[str, Path] = {}
        cmd_names: dict[str, Path] = {}
        mcp_names: dict[str, Path] = {}
        for pdir in plugin_dirs:
            manifest_path = pdir / "plugin.json"
            if not manifest_path.is_file():
                continue
            try:
                manifest = json.loads(manifest_path.read_text())
            except json.JSONDecodeError:
                continue
            name = manifest.get("name", "")
            if name and name in names:
                self.fail(f"duplicate plugin name '{name}' in {pdir} and {names[name]}")
            if name:
                names[name] = pdir
            commands_path = pdir / _first(manifest.get("commands", "commands"), "commands")
            if commands_path.is_dir():
                for cmd in commands_path.glob("*.md"):
                    if cmd.stem in cmd_names:
                        self.fail(f"duplicate command '{cmd.stem}' in {pdir} and {cmd_names[cmd.stem]}")
                    cmd_names[cmd.stem] = pdir
            mcp_value = manifest.get("mcpServers", ".mcp.json")
            if isinstance(mcp_value, str):
                mcp_path = pdir / mcp_value
                if mcp_path.is_file():
                    try:
                        cfg = json.loads(mcp_path.read_text())
                        for server_name in (cfg.get("servers") or {}).keys():
                            if server_name in mcp_names:
                                self.fail(f"duplicate MCP server '{server_name}' in {pdir} and {mcp_names[server_name]}")
                            mcp_names[server_name] = pdir
                    except json.JSONDecodeError:
                        pass

    def validate_marketplace(self) -> None:
        mp = self.repo / ".github" / "plugin" / "marketplace.json"
        if not mp.is_file():
            return
        try:
            data = json.loads(mp.read_text())
        except json.JSONDecodeError as exc:
            self.fail(f"{mp}: invalid JSON: {exc}")
            return
        for err in sorted(self.marketplace_validator.iter_errors(data), key=lambda e: list(e.path)):
            self.fail(f"{mp}: schema: {err.message}")
        for entry in data.get("plugins", []):
            src = entry.get("source", "")
            if isinstance(src, str) and not (self.repo / src).is_dir():
                self.fail(f"{mp}: plugin '{entry.get('name')}' source '{src}' not found")

    def validate_template(self, template_dir: Path) -> None:
        tpl = template_dir / "TEMPLATE.md"
        if not tpl.is_file():
            self.fail(f"{template_dir.relative_to(self.repo)}: missing TEMPLATE.md")
            return
        fm = parse_frontmatter(tpl.read_text())
        for key in ("name", "description", "version", "category"):
            if not fm.get(key):
                self.fail(f"{tpl}: missing frontmatter '{key}'")

    def run(self) -> int:
        plugins_dir = self.repo / "plugins"
        plugin_dirs = sorted(d for d in plugins_dir.iterdir() if d.is_dir()) if plugins_dir.is_dir() else []
        for d in plugin_dirs:
            self.validate_plugin(d)
        self.check_global_uniqueness(plugin_dirs)
        self.validate_marketplace()
        templates_dir = self.repo / "templates"
        if templates_dir.is_dir():
            for d in sorted(t for t in templates_dir.iterdir() if t.is_dir()):
                self.validate_template(d)
        for w in self.warnings:
            print(f"WARN: {w}", file=sys.stderr)
        for e in self.errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1 if self.errors else 0


if __name__ == "__main__":
    sys.exit(Validator(REPO_ROOT).run())
