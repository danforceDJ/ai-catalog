from __future__ import annotations
import importlib.util
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_zip_directory_roundtrip(tmp_path):
    mod = _load("generate_zips")
    src = tmp_path / "sample"
    (src / "nested").mkdir(parents=True)
    (src / "a.txt").write_text("alpha")
    (src / "nested" / "b.txt").write_text("beta")
    dst = tmp_path / "out.zip"
    size = mod.zip_directory(src, dst)
    assert dst.is_file()
    assert size > 0
    with zipfile.ZipFile(dst) as zf:
        names = sorted(zf.namelist())
    assert names == ["sample/a.txt", "sample/nested/b.txt"]
