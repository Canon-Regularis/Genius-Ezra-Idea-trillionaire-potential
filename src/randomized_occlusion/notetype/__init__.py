"""Definition, assembly, and installation of the add-on's note type."""

from __future__ import annotations

from .installer import InstallResult, NoteTypeInstaller
from .spec import DEFAULT_SPEC, NoteTypeSpec
from .templates import TemplateAssembler, extract_fingerprint

__all__ = [
    "DEFAULT_SPEC",
    "InstallResult",
    "NoteTypeInstaller",
    "NoteTypeSpec",
    "TemplateAssembler",
    "extract_fingerprint",
]
