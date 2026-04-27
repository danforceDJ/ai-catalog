#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Scaffold a new catalog item in one command.

Usage examples
--------------
  # Minimal – prompts for nothing, creates sensible defaults:
  uv run --script system/scripts/scaffold.py mcp --name my-server

  # With full metadata (no prompts at all):
  uv run --script system/scripts/scaffold.py mcp --name my-server \\
      --description "My awesome MCP server" --category integrations \\
      --tags "my-server,mcp" --keywords "my-server,ai" --author "yourGitHubHandle"

  # Other asset types:
  uv run --script system/scripts/scaffold.py skill  --name my-skill
  uv run --script system/scripts/scaffold.py agent  --name my-agent
  uv run --script system/scripts/scaffold.py prompt --name my-prompt

After scaffolding
-----------------
  1. Fill in the generated file(s) with real values.
  2. uv run --script system/scripts/validate_catalog.py
  3. uv run --script system/scripts/sync_catalog.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
KEBAB_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _kebab(name: str) -> str:
    if not KEBAB_RE.match(name):
        sys.exit(
            f"Error: name '{name}' must be kebab-case (lowercase letters, digits, hyphens), "
            "max 64 chars."
        )
    return name


def _write(path: Path, content: str, force: bool) -> None:
    existed = path.exists()
    if existed and not force:
        print(f"  [skip]   {path.relative_to(REPO_ROOT)}  (already exists; use --force to overwrite)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    status = "[overwrite]" if existed else "[create]"
    print(f"  {status}  {path.relative_to(REPO_ROOT)}")


def _plugin_json(name: str, args: argparse.Namespace, **extra_fields) -> str:
    manifest: dict = {
        "name": name,
        "description": args.description or f"TODO: describe {name}.",
        "version": args.version or "1.0.0",
    }
    if args.author:
        manifest["author"] = {"name": args.author}
    manifest["license"] = args.license or "MIT"
    manifest["keywords"] = _csv(args.keywords) or [name]
    manifest["category"] = args.category or "integrations"
    manifest["tags"] = _csv(args.tags) or [name]
    manifest.update(extra_fields)
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _next_steps(*lines: str) -> None:
    print("\nNext steps:")
    for i, line in enumerate(lines, 1):
        print(f"  {i}. {line}")


# ---------------------------------------------------------------------------
# Scaffold handlers
# ---------------------------------------------------------------------------

def scaffold_mcp(args: argparse.Namespace) -> None:
    """Create catalog/mcp/<name>/.mcp.json + catalog/plugins/<name>/plugin.json."""
    name = _kebab(args.name)

    # --- .mcp.json template --------------------------------------------------
    mcp_template = {
        "servers": {
            name: {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", f"{name}@latest"],
                # "env": {"MY_ENV_VAR": "value"}  # add env vars if needed
            }
        }
    }
    _write(
        REPO_ROOT / "catalog" / "mcp" / name / ".mcp.json",
        json.dumps(mcp_template, indent=2, ensure_ascii=False) + "\n",
        args.force,
    )

    # --- plugin.json ----------------------------------------------------------
    _write(
        REPO_ROOT / "catalog" / "plugins" / name / "plugin.json",
        _plugin_json(name, args, mcpServers=[name]),
        args.force,
    )

    _next_steps(
        f"Edit  catalog/mcp/{name}/.mcp.json  — set the real server command/args",
        f"Edit  catalog/plugins/{name}/plugin.json  — update description, tags, keywords",
        "uv run --script system/scripts/validate_catalog.py",
        "uv run --script system/scripts/sync_catalog.py",
    )


def scaffold_skill(args: argparse.Namespace) -> None:
    """Create catalog/skills/<name>/SKILL.md + catalog/plugins/<name>/plugin.json."""
    name = _kebab(args.name)
    desc = args.description or f"TODO: describe {name}."
    version = args.version or "1.0.0"

    skill_md = textwrap.dedent(f"""\
        ---
        name: {name}
        description: {desc}
        version: {version}
        category: {args.category or "skills"}
        tags: [{", ".join(_csv(args.tags) or [name])}]
        keywords: [{", ".join(_csv(args.keywords) or [name])}]
        ---

        # {name.replace("-", " ").title()}

        TODO: describe what this skill does and how to use it.

        ## Usage

        TODO: provide usage instructions.

        ## Examples

        TODO: add examples.
    """)
    _write(REPO_ROOT / "catalog" / "skills" / name / "SKILL.md", skill_md, args.force)

    _write(
        REPO_ROOT / "catalog" / "plugins" / name / "plugin.json",
        _plugin_json(name, args, skills=[name]),
        args.force,
    )

    _next_steps(
        f"Edit  catalog/skills/{name}/SKILL.md  — fill in instructions and examples",
        f"Edit  catalog/plugins/{name}/plugin.json  — update description, tags, keywords",
        "uv run --script system/scripts/validate_catalog.py",
        "uv run --script system/scripts/sync_catalog.py",
    )


def scaffold_agent(args: argparse.Namespace) -> None:
    """Create catalog/agents/<name>.agent.md + catalog/plugins/<name>/plugin.json."""
    name = _kebab(args.name)
    desc = args.description or f"TODO: describe {name}."
    version = args.version or "1.0.0"

    agent_md = textwrap.dedent(f"""\
        ---
        name: {name}
        description: {desc}
        version: {version}
        ---

        # {name.replace("-", " ").title()}

        TODO: describe the agent's role, persona, and capabilities.

        ## Instructions

        TODO: provide detailed instructions for the agent.

        ## Constraints

        - TODO: list constraints and guardrails.
    """)
    _write(REPO_ROOT / "catalog" / "agents" / f"{name}.agent.md", agent_md, args.force)

    _write(
        REPO_ROOT / "catalog" / "plugins" / name / "plugin.json",
        _plugin_json(name, args, agents=[name]),
        args.force,
    )

    _next_steps(
        f"Edit  catalog/agents/{name}.agent.md  — fill in the agent instructions",
        f"Edit  catalog/plugins/{name}/plugin.json  — update description, tags, keywords",
        "uv run --script system/scripts/validate_catalog.py",
        "uv run --script system/scripts/sync_catalog.py",
    )


def scaffold_prompt(args: argparse.Namespace) -> None:
    """Create catalog/prompts/<name>.md + catalog/plugins/<name>/plugin.json."""
    name = _kebab(args.name)
    desc = args.description or f"TODO: describe {name}."
    version = args.version or "1.0.0"

    prompt_md = textwrap.dedent(f"""\
        ---
        name: {name}
        description: {desc}
        version: {version}
        ---

        TODO: write the prompt body here.

        ${{input}}
    """)
    _write(REPO_ROOT / "catalog" / "prompts" / f"{name}.md", prompt_md, args.force)

    _write(
        REPO_ROOT / "catalog" / "plugins" / name / "plugin.json",
        _plugin_json(name, args, commands=[name]),
        args.force,
    )

    _next_steps(
        f"Edit  catalog/prompts/{name}.md  — write the actual prompt",
        f"Edit  catalog/plugins/{name}/plugin.json  — update description, tags, keywords",
        "uv run --script system/scripts/validate_catalog.py",
        "uv run --script system/scripts/sync_catalog.py",
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

HANDLERS = {
    "mcp": scaffold_mcp,
    "skill": scaffold_skill,
    "agent": scaffold_agent,
    "prompt": scaffold_prompt,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Scaffold a new catalog item.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              uv run --script system/scripts/scaffold.py mcp --name github-mcp
              uv run --script system/scripts/scaffold.py skill --name summarize-pr \\
                  --description "Summarise a pull request" --category productivity
              uv run --script system/scripts/scaffold.py agent --name code-reviewer
              uv run --script system/scripts/scaffold.py prompt --name explain-error
        """),
    )
    p.add_argument("type", choices=list(HANDLERS), help="Type of catalog item to scaffold")
    p.add_argument("--name", required=True, help="Kebab-case name (≤64 chars)")
    p.add_argument("--description", help="Short description (shown in marketplace)")
    p.add_argument("--version", default="1.0.0", help="Semantic version (default: 1.0.0)")
    p.add_argument("--author", help="Author GitHub handle or name")
    p.add_argument("--license", default="MIT", help="SPDX license identifier (default: MIT)")
    p.add_argument("--category", help="Category (e.g. integrations, productivity, devtools)")
    p.add_argument("--tags", help="Comma-separated tags (e.g. 'aws,cloud,mcp')")
    p.add_argument("--keywords", help="Comma-separated keywords")
    p.add_argument("--force", action="store_true", help="Overwrite existing files")
    return p


def main() -> None:
    args = build_parser().parse_args()
    print(f"Scaffolding {args.type}: {args.name}")
    HANDLERS[args.type](args)


if __name__ == "__main__":
    main()

