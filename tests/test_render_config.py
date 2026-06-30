from __future__ import annotations

import json

from randomized_occlusion.config.defaults import DEFAULT_CONFIG
from randomized_occlusion.config.render_config import RenderConfig


def test_from_mapping_fills_missing_with_defaults():
    rc = RenderConfig.from_mapping({"accent_color": "#000000"})
    assert rc.accent_color == "#000000"
    assert rc.min_arrow_fraction == DEFAULT_CONFIG["min_arrow_fraction"]


def test_behaviour_json_uses_camel_case_keys():
    rc = RenderConfig.from_mapping(DEFAULT_CONFIG)
    data = json.loads(rc.behaviour_json())
    assert set(data) == {
        "minArrowFraction",
        "showTargetDot",
        "promptText",
        "maxPlacementAttempts",
    }


def test_css_variables_cover_all_colors():
    rc = RenderConfig.from_mapping(DEFAULT_CONFIG)
    variables = rc.css_variables()
    assert variables["--ro-accent"] == DEFAULT_CONFIG["accent_color"]
    assert set(variables) == {"--ro-accent", "--ro-box-fill", "--ro-box-text", "--ro-dot"}


def test_fingerprint_payload_changes_with_values():
    a = RenderConfig.from_mapping(DEFAULT_CONFIG).fingerprint_payload()
    b = RenderConfig.from_mapping({**DEFAULT_CONFIG, "accent_color": "#123456"}).fingerprint_payload()
    assert a != b
