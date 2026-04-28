#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Generate VS Code workspace AI customization files from catalog."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def write_vscode_mcp_json() -> None:
    """Merge all mcpServers/*/.mcp.json files into .vscode/mcp.json."""
    mcp_servers_dir = REPO_ROOT / "mcp"
    merged_servers = {}

    if not mcp_servers_dir.exists():
        return

    for server_dir in sorted(mcp_servers_dir.iterdir()):
        if not server_dir.is_dir():
            continue

        mcp_file = server_dir / ".mcp.json"
        if not mcp_file.exists():
            continue

        try:
            with open(mcp_file) as f:
                data = json.load(f)

            if "servers" in data:
                for server_name, server_config in data["servers"].items():
                    if server_name in merged_servers:
                        print(
                            f"Warning: MCP server '{server_name}' defined in multiple locations. "
                            f"Using {server_dir.name}",
                            file=sys.stderr,
                        )
                    merged_servers[server_name] = server_config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to read {mcp_file}: {e}", file=sys.stderr)

    vscode_dir = REPO_ROOT / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)

    output_file = vscode_dir / "mcp.json"
    with open(output_file, "w") as f:
        json.dump({"servers": merged_servers}, f, indent=2)


def write_github_prompts() -> None:
    """Convert commands/*.md to .github/prompts/*.prompt.md with VS Code format."""
    commands_dir = REPO_ROOT / "prompts"
    if not commands_dir.exists():
        return

    prompts_dir = REPO_ROOT / ".github" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    for cmd_file in sorted(commands_dir.glob("*.md")):
        with open(cmd_file) as f:
            content = f.read()

        match = FRONTMATTER_PATTERN.match(content)
        old_frontmatter_dict = {}
        body = content

        if match:
            try:
                old_frontmatter_dict = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                pass
            body = content[match.end() :]

        new_frontmatter_dict = {"mode": "ask"}
        if "description" in old_frontmatter_dict:
            new_frontmatter_dict["description"] = old_frontmatter_dict[
                "description"
            ]

        frontmatter_yaml = yaml.safe_dump(
            new_frontmatter_dict, default_flow_style=False, sort_keys=False, width=4096
        ).rstrip()

        output_file = prompts_dir / f"{cmd_file.stem}.prompt.md"
        with open(output_file, "w") as f:
            f.write(f"---\n{frontmatter_yaml}\n---\n\n{body}")


def write_github_instructions() -> None:
    """Concatenate all agents/*.agent.md bodies into .github/instructions/catalog-agent.instructions.md."""
    agents_dir = REPO_ROOT / "agents"
    if not agents_dir.exists():
        return

    instructions_dir = REPO_ROOT / ".github" / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)

    agent_bodies = []

    for agent_file in sorted(agents_dir.glob("*.agent.md")):
        with open(agent_file) as f:
            content = f.read()

        match = FRONTMATTER_PATTERN.match(content)
        body = content

        if match:
            body = content[match.end() :]

        agent_bodies.append(body.strip())

    merged_content = "\n\n".join(agent_bodies)

    output_file = instructions_dir / "catalog-agent.instructions.md"
    frontmatter = yaml.safe_dump(
        {"applyTo": "**"}, default_flow_style=False, sort_keys=False, width=4096
    ).rstrip()

    with open(output_file, "w") as f:
        f.write(f"---\n{frontmatter}\n---\n\n{merged_content}\n")


def main() -> None:
    """Generate all VS Code artifacts."""
    write_vscode_mcp_json()
    write_github_prompts()
    write_github_instructions()
    print("Generated VS Code artifacts")


if __name__ == "__main__":
    main()
