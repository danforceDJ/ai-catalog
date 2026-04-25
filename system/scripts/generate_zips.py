#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Produce one zip per plugin and per template under docs/dl/."""
from __future__ import annotations
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ONE_MB = 1_048_576


def zip_directory(src: Path, dst: Path) -> int:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=str(path.relative_to(src.parent)))
    return dst.stat().st_size


def main() -> None:
    out_dir = REPO_ROOT / "docs" / "dl"
    out_dir.mkdir(parents=True, exist_ok=True)
    sources: list[Path] = []
    for parent in (("catalog", "plugins"), ("catalog", "templates")):
        base = REPO_ROOT / Path(*parent)
        if base.is_dir():
            sources.extend(sorted(d for d in base.iterdir() if d.is_dir()))
    for src in sources:
        dst = out_dir / f"{src.name}.zip"
        size = zip_directory(src, dst)
        flag = " (WARN: >1MB)" if size > ONE_MB else ""
        print(f"{dst.relative_to(REPO_ROOT)}: {size} bytes{flag}")


if __name__ == "__main__":
    main()
