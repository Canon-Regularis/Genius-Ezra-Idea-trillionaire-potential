#!/usr/bin/env python3
"""Package the add-on into a distributable ``.ankiaddon`` zip.

An ``.ankiaddon`` file is a plain zip whose *root* contains ``__init__.py`` (no
wrapping folder). This script zips the contents of ``src/randomized_occlusion/``
into ``dist/randomized_occlusion.ankiaddon``, skipping caches and dev artefacts.

Usage:
    python build.py
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = ROOT / "src" / "randomized_occlusion"
DIST_DIR = ROOT / "dist"
OUTPUT = DIST_DIR / "randomized_occlusion.ankiaddon"

# Files/dirs that must never ship inside the add-on.
EXCLUDED_NAMES = {"__pycache__", "meta.json", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def _included(path: Path) -> bool:
    if any(part in EXCLUDED_NAMES for part in path.parts):
        return False
    return path.suffix not in EXCLUDED_SUFFIXES


def _read_version() -> str:
    """The single source of truth for the version, read without importing aqt.

    ``_version.py`` is standalone, so exec-ing it in an isolated namespace avoids
    importing the package (whose ``__init__`` would try to reach Anki).
    """
    namespace: dict[str, object] = {}
    exec((PACKAGE_DIR / "_version.py").read_text(encoding="utf-8"), namespace)
    return str(namespace["__version__"])


def _manifest_bytes(path: Path, version: str) -> bytes:
    """The manifest with ``human_version`` stamped from ``_version.py``.

    Stamping at build time means the shipped ``.ankiaddon`` can never advertise a
    version that has drifted from the source of truth.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    data["human_version"] = version
    return (json.dumps(data, indent=2) + "\n").encode("utf-8")


def build() -> Path:
    if not PACKAGE_DIR.is_dir():
        raise SystemExit(f"package directory not found: {PACKAGE_DIR}")

    version = _read_version()
    DIST_DIR.mkdir(exist_ok=True)
    if OUTPUT.exists():
        OUTPUT.unlink()

    count = 0
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_DIR.rglob("*")):
            if not path.is_file() or not _included(path):
                continue
            arcname = path.relative_to(PACKAGE_DIR).as_posix()
            if arcname == "manifest.json":
                archive.writestr(arcname, _manifest_bytes(path, version))
            else:
                archive.write(path, arcname)
            count += 1

    print(f"Wrote {OUTPUT.relative_to(ROOT)} v{version} ({count} files)")
    return OUTPUT


if __name__ == "__main__":
    build()
