"""Filesystem access to bundled web assets.

Add-ons installed from AnkiWeb live in a folder named by a numeric id, so the
package name is not stable. We therefore locate bundled files relative to this
module's own location rather than via a hard-coded package name.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
_WEB_DIR = _PACKAGE_DIR / "web"


@lru_cache(maxsize=None)
def read_web(relative_path: str) -> str:
    """Read a UTF-8 text asset under ``web/`` (e.g. ``"review/render.js"``)."""
    path = _WEB_DIR / relative_path
    return path.read_text(encoding="utf-8")


def package_dir() -> Path:
    return _PACKAGE_DIR


def user_files_dir() -> Path:
    """The ``user_files/`` directory, the only one preserved across upgrades."""
    path = _PACKAGE_DIR / "user_files"
    path.mkdir(exist_ok=True)
    return path
