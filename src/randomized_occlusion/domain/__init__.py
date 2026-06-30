"""Pure, Anki-independent domain model for randomized image occlusion."""

from __future__ import annotations

from .geometry import NormalizedPoint
from .structure import Structure
from .structure_set import StructureSet

__all__ = ["NormalizedPoint", "Structure", "StructureSet"]
