"""Adapters and factories bridging the domain model to Anki's collection."""

from __future__ import annotations

from .gateways import (
    AnkiMediaGateway,
    AnkiModelGateway,
    MediaGateway,
    ModelGateway,
    image_field_html,
)
from .note_factory import NoteContent, NoteFactory

__all__ = [
    "AnkiMediaGateway",
    "AnkiModelGateway",
    "MediaGateway",
    "ModelGateway",
    "NoteContent",
    "NoteFactory",
    "image_field_html",
]
