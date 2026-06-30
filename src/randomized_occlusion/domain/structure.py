"""The core domain entity: a labelled structure on an image."""

from __future__ import annotations

from dataclasses import dataclass

from .geometry import NormalizedPoint


@dataclass(frozen=True, slots=True)
class Structure:
    """A single labelled point on an image.

    A structure is the *thing being tested*: a fixed location on the image (the
    ``target``) together with the ``label`` that correctly identifies it. The
    ``ordinal`` is a 1-based index that ties the structure to exactly one
    generated card (via an Anki cloze ordinal) so that "hide one, guess one"
    review works.

    Crucially, a structure stores *only* the fixed target location. Where the
    prompt box is drawn is decided at review time by the renderer and is never
    persisted — that is what makes placement randomisable.
    """

    ordinal: int
    target: NormalizedPoint
    label: str

    def __post_init__(self) -> None:
        if self.ordinal < 1:
            raise ValueError(f"ordinal must be >= 1, got {self.ordinal}")
        if not self.label or not self.label.strip():
            raise ValueError("label must be a non-empty string")

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-friendly dict consumed by the reviewer JS."""
        return {
            "ord": self.ordinal,
            "x": self.target.x,
            "y": self.target.y,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Structure:
        return cls(
            ordinal=int(data["ord"]),  # type: ignore[arg-type]
            target=NormalizedPoint(x=float(data["x"]), y=float(data["y"])),  # type: ignore[arg-type]
            label=str(data["label"]),
        )
