from __future__ import annotations

import json
from pathlib import Path

import randomized_occlusion
from randomized_occlusion._version import __version__


def _manifest() -> dict:
    path = Path(randomized_occlusion.__file__).parent / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_manifest_human_version_matches_version_module():
    # _version.py is the single source of truth; the manifest must not drift.
    # (build.py also re-stamps this, but keeping the source in sync means the
    # symlink dev install and the built artifact always agree.)
    assert _manifest()["human_version"] == __version__


def test_manifest_declares_the_required_fields():
    manifest = _manifest()
    assert manifest["package"] == "randomized_occlusion"
    assert manifest["name"] == "Randomized Image Occlusion"
    # Anki 23.10 introduced the modern add-on APIs this add-on relies on.
    assert manifest["min_point_version"] == 231000
    assert manifest["homepage"].startswith("https://")
