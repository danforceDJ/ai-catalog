#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jinja2>=3"]
# ///
"""Render docs/index.html from catalog.json + Jinja template."""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_URL = "https://github.com/danforceDJ/ai-catalog"


def score_item(item: dict, q: str) -> int:
    if not q:
        return 1
    q = q.lower()
    name = (item.get("name") or "").lower()
    desc = (item.get("description") or "").lower()
    kw = [str(k).lower() for k in (item.get("keywords") or [])]
    tags = [str(t).lower() for t in (item.get("tags") or [])]
    s = 0
    if name.startswith(q):
        s += 3
    elif q in name:
        s += 2
    if q in kw or q in tags:
        s += 2
    if q in desc:
        s += 1
    return s


def render_site(catalog: dict, out_path: Path, scripts_dir: Path | None = None) -> None:
    scripts_dir = scripts_dir or (REPO_ROOT / "system" / "scripts")
    env = Environment(
        loader=FileSystemLoader(scripts_dir / "templates"),
        autoescape=select_autoescape(enabled_extensions=("j2",)),
    )
    template = env.get_template("index.html.j2")
    catalog_json = json.dumps(catalog, ensure_ascii=False)
    generated_at = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    html = template.render(
        generated_at=generated_at,
        repo_url=REPO_URL,
        repo_url_json=json.dumps(REPO_URL),
        catalog_json=catalog_json,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)


def main() -> None:
    catalog = json.loads((REPO_ROOT / "system" / "artifacts" / "catalog.json").read_text())
    render_site(catalog, REPO_ROOT / "docs" / "index.html")
    print(f"Wrote docs/index.html ({len(catalog['plugins'])} plugins, {len(catalog['templates'])} templates)")


if __name__ == "__main__":
    main()
