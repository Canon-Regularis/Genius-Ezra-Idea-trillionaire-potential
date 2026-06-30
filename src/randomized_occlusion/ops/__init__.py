"""Collection-mutating operations (undo-safe, run off the UI thread)."""

from __future__ import annotations

from .create_note import NoteRequest, add_randomized_occlusion_note

__all__ = ["NoteRequest", "add_randomized_occlusion_note"]
