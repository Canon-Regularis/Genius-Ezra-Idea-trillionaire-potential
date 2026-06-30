#!/usr/bin/env python3
"""Package the add-on into a distributable ``.ankiaddon`` zip.

An ``.ankiaddon`` file is a plain zip whose *root* contains ``__init__.py`` (no
wrapping folder). This script zips the contents of ``src/randomized_occlusion/``
into ``dist/randomized_occlusion.ankiaddon``, skipping caches and dev artefacts.

Usage:
    python build.py
"""

from __future__ import annotations

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


def build() -> Path:
    if not PACKAGE_DIR.is_dir():
        raise SystemExit(f"package directory not found: {PACKAGE_DIR}")

    DIST_DIR.mkdir(exist_ok=True)
    if OUTPUT.exists():
        OUTPUT.unlink()

    count = 0
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_DIR.rglob("*")):
            if not path.is_file() or not _included(path):
                continue
            archive.write(path, path.relative_to(PACKAGE_DIR).as_posix())
            count += 1

    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({count} files)")
    return OUTPUT


if __name__ == "__main__":
    build()
