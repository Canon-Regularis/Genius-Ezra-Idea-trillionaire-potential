"""The subset of configuration that shapes how a card renders.

``RenderConfig`` is the single translation point between the add-on's snake_case
Python config and the two representations the card needs:
  * a camelCase JSON blob the reviewer JavaScript reads, and
  * a set of CSS custom properties the note-type stylesheet reads.

Centralising this mapping (rather than scattering string keys across the
template code) keeps the JS/CSS contract in one auditable place.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from .defaults import DEFAULT_CONFIG


@dataclass(frozen=True, slots=True)
class RenderConfig:
    min_arrow_fraction: float
    show_target_dot: bool
    prompt_text: str
    max_placement_attempts: int
    accent_color: str
    box_fill: str
    box_text_color: str
    target_dot_color: str

    @classmethod
    def from_mapping(cls, config: Mapping[str, Any]) -> RenderConfig:
        """Build from a (possibly partial) config mapping, filling gaps with
        defaults and coercing to the declared types."""

        def get(key: str) -> Any:
            return config.get(key, DEFAULT_CONFIG[key])

        return cls(
            min_arrow_fraction=float(get("min_arrow_fraction")),
            show_target_dot=bool(get("show_target_dot")),
            prompt_text=str(get("prompt_text")),
            max_placement_attempts=int(get("max_placement_attempts")),
            accent_color=str(get("accent_color")),
            box_fill=str(get("box_fill")),
            box_text_color=str(get("box_text_color")),
            target_dot_color=str(get("target_dot_color")),
        )

    def behaviour_json(self) -> str:
        """Compact JSON read by ``render.js`` from the ``#ro-config`` element."""
        return json.dumps(
            {
                "minArrowFraction": self.min_arrow_fraction,
                "showTargetDot": self.show_target_dot,
                "promptText": self.prompt_text,
                "maxPlacementAttempts": self.max_placement_attempts,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def css_variables(self) -> dict[str, str]:
        """CSS custom properties injected onto ``.ro-root``."""
        return {
            "--ro-accent": self.accent_color,
            "--ro-box-fill": self.box_fill,
            "--ro-box-text": self.box_text_color,
            "--ro-dot": self.target_dot_color,
        }

    def fingerprint_payload(self) -> str:
        """A stable string capturing every value, for change detection."""
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)
