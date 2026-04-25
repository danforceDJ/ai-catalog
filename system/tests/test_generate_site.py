from __future__ import annotations
import importlib.util
import json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


SAMPLE_CATALOG = {
    "plugins": [
        {
            "name": "sample-skill", "description": "A sample.", "version": "1.0.0",
            "type": "skill", "category": "testing", "tags": ["demo"], "keywords": ["foo"],
            "components": {"skills": ["sample-skill"], "agents": [], "commands": [], "mcpServers": [], "hooks": False},
            "install": {
                "copilot": "sample-skill@ai-catalog", "vscodeMcpDeeplink": None,
                "rawFiles": ["skills/sample-skill/SKILL.md"], "zip": "dl/sample-skill.zip",
                "repoPath": "plugins/sample-skill",
            },
        }
    ],
    "templates": [
        {
            "name": "sample-template", "description": "A tpl.", "version": "1.0.0",
            "type": "template", "category": "docs", "tags": [], "keywords": [],
            "install": {"rawFiles": ["TEMPLATE.md"], "zip": "dl/sample-template.zip", "repoPath": "templates/sample-template"},
        }
    ],
}


def test_render_site_contains_cards_and_search(tmp_path):
    mod = _load("generate_site")
    out = tmp_path / "index.html"
    mod.render_site(SAMPLE_CATALOG, out, template_dir=SCRIPTS.parent / "web")
    html = out.read_text()
    assert "sample-skill" in html
    assert "sample-template" in html
    assert 'id="search-input"' in html
    assert 'data-type="skill"' in html
    assert "charset=\"UTF-8\"" in html or "charset=\"utf-8\"" in html.lower()


def test_scoring_function():
    mod = _load("generate_site")
    items = SAMPLE_CATALOG["plugins"] + SAMPLE_CATALOG["templates"]
    scored = [(mod.score_item(it, "sample"), it["name"]) for it in items]
    assert all(s > 0 for s, _ in scored)
    assert mod.score_item(items[0], "SKILL") > 0
    assert mod.score_item(items[0], "nomatch") == 0
