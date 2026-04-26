#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "jinja2>=3"]
# ///
"""Run all catalog generators in the correct order with a single command.

Usage:
  uv run --script system/scripts/sync_catalog.py
  uv run --script system/scripts/sync_catalog.py --no-validate
  uv run --script system/scripts/sync_catalog.py --include-zips
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "system" / "scripts"

GENERATORS = [
    "generate_marketplace.py",
    "generate_catalog.py",
    "generate_claude_marketplace.py",
    "generate_vscode_artifacts.py",
]
OPTIONAL = ["generate_zips.py", "generate_site.py"]
VALIDATOR = "validate_catalog.py"


def run_script(script: str, label: str | None = None) -> bool:
    path = SCRIPTS_DIR / script
    display = label or script
    print(f"  > {display} ...", end=" ", flush=True)
    t0 = time.monotonic()
    result = subprocess.run(["uv", "run", "--script", str(path)], capture_output=True, text=True)
    elapsed = time.monotonic() - t0
    if result.returncode == 0:
        summary = next((line for line in reversed(result.stdout.splitlines()) if line.strip()), "")
        print(f"OK  [{elapsed:.1f}s]  {summary}")
        return True
    print(f"FAILED  [{elapsed:.1f}s]")
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip(), file=sys.stderr)
    return False


def main() -> None:
    p = argparse.ArgumentParser(description="Run all catalog generators and validate.")
    p.add_argument("--no-validate", action="store_true", help="Skip validation after generation")
    p.add_argument("--include-zips", action="store_true", help="Also run generate_zips + generate_site (slow)")
    p.add_argument("--skip", metavar="SCRIPT", action="append", default=[], help="Skip a generator by filename")
    args = p.parse_args()

    scripts = list(GENERATORS)
    if args.include_zips:
        scripts.extend(OPTIONAL)
    scripts = [s for s in scripts if s not in args.skip]

    print(f"sync_catalog — running {len(scripts)} generator(s)\n")
    failed: list[str] = []
    for script in scripts:
        if not run_script(script):
            failed.append(script)

    if not args.no_validate:
        print()
        if not run_script(VALIDATOR, "validate_catalog.py (validation)"):
            failed.append(VALIDATOR)

    print()
    if failed:
        print(f"FAILED: {len(failed)} step(s) failed: {', '.join(failed)}")
        sys.exit(1)
    print("Done. Commit the regenerated artefacts with your changes.")


if __name__ == "__main__":
    main()

