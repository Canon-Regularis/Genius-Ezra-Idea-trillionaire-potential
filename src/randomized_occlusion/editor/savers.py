"""Persistence strategies for the marking dialog.

The marking dialog gathers the same thing every time — a :class:`MarkupResult`
(structures, options, header/back text, and which image to use). *What happens
to it on Save* varies, so that is a Strategy:

* :class:`CreateNoteSaver` — add a brand-new note (Tools → menu flow).
* :class:`UpdateNoteSaver` — rewrite an existing note (Browser edit flow).
* :class:`EditorFieldSaver` — write the fields into a note being composed in
  Anki's own Add window, letting Anki add it (so occlusion cards are made with
  the canvas instead of the raw fields).

Keeping this out of the dialog means the dialog has no idea how notes are stored,
and each flow is a small, single-responsibility object.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from aqt.utils import showWarning

from ..collection.gateways import AnkiMediaGateway
from ..collection.note_factory import NoteFactory
from ..config.config_service import ConfigService
from ..domain.card_options import CardOptions
from ..domain.structure_set import StructureSet
from ..notetype.spec import DEFAULT_SPEC, NoteTypeSpec
from ..ops.create_note import NoteRequest, add_randomized_occlusion_note
from ..ops.update_note import UpdateRequest, update_randomized_occlusion_note

__all__ = [
    "CreateNoteSaver",
    "EditorFieldSaver",
    "MarkupResult",
    "NoteSaver",
    "UpdateNoteSaver",
]


@dataclass(frozen=True, slots=True)
class MarkupResult:
    """The validated output of a marking session, ready to be persisted."""

    structures: StructureSet
    options: CardOptions
    header: str
    back_extra: str
    # A freshly chosen file to import, or None to keep the existing image.
    new_image_path: str | None
    existing_image_filename: str | None
    # Only meaningful when the saver wants a deck (creation).
    deck_name: str | None


def _cards(count: int) -> str:
    return f"{count} card{'s' if count != 1 else ''}"


class NoteSaver(ABC):
    """Turns a :class:`MarkupResult` into a persisted (or staged) note."""

    #: Whether the dialog should offer a deck picker (only creation does).
    wants_deck: bool = False

    def title(self) -> str:
        return "Randomized Image Occlusion"

    def load_button_label(self) -> str:
        return "Load image…"

    @abstractmethod
    def save(self, dialog: Any, result: MarkupResult) -> None:
        """Persist ``result``. Implementations close ``dialog`` when done via
        ``dialog.finish_saved(message)`` (possibly from an async callback)."""


class CreateNoteSaver(NoteSaver):
    """Adds a brand-new note via the undo-safe create op."""

    wants_deck = True

    def __init__(self, config: ConfigService, spec: NoteTypeSpec = DEFAULT_SPEC) -> None:
        self._config = config
        self._spec = spec

    def save(self, dialog: Any, result: MarkupResult) -> None:
        deck = result.deck_name or "Default"
        self._config.set_deck(deck)
        request = NoteRequest(
            image_path=result.new_image_path or "",
            structures=result.structures,
            deck_name=deck,
            options=result.options,
            header=result.header,
            back_extra=result.back_extra,
        )
        count = len(result.structures)
        add_randomized_occlusion_note(
            parent=dialog,
            request=request,
            render_config=self._config.render_config(),
            spec=self._spec,
            on_success=lambda _changes: dialog.finish_saved(f"Added {_cards(count)}."),
        )


class UpdateNoteSaver(NoteSaver):
    """Rewrites an existing note via the undo-safe update op."""

    def __init__(
        self, config: ConfigService, note_id: int, spec: NoteTypeSpec = DEFAULT_SPEC
    ) -> None:
        self._config = config
        self._note_id = note_id
        self._spec = spec

    def title(self) -> str:
        return "Edit Randomized Image Occlusion"

    def load_button_label(self) -> str:
        return "Replace image…"

    def save(self, dialog: Any, result: MarkupResult) -> None:
        request = UpdateRequest(
            note_id=self._note_id,
            structures=result.structures,
            existing_image_filename=result.existing_image_filename or "",
            options=result.options,
            new_image_path=result.new_image_path,
            header=result.header,
            back_extra=result.back_extra,
        )
        update_randomized_occlusion_note(
            parent=dialog,
            request=request,
            render_config=self._config.render_config(),
            spec=self._spec,
            on_success=lambda _changes: dialog.finish_saved("Card updated."),
        )


class EditorFieldSaver(NoteSaver):
    """Stages the markup into a note being composed in Anki's own editor.

    Instead of adding the note itself, it imports the image, builds the field
    values with the shared :class:`NoteFactory`, writes them onto the editor's
    in-progress note, and reloads the editor — so Anki's normal **Add** button
    creates the card. This is what lets the Add window show the marking canvas
    rather than the raw occlusion fields.
    """

    def __init__(
        self,
        config: ConfigService,
        main_window: Any,
        editor: Any,
        spec: NoteTypeSpec = DEFAULT_SPEC,
    ) -> None:
        self._config = config
        self._mw = main_window
        self._editor = editor
        self._spec = spec

    def load_button_label(self) -> str:
        return "Replace image…"

    def save(self, dialog: Any, result: MarkupResult) -> None:
        col = self._mw.col
        note = getattr(self._editor, "note", None)
        if col is None or note is None:
            # The Add window/collection went away between opening the canvas and
            # saving; tell the user rather than fail silently.
            showWarning(
                "Couldn't prepare the card — the Add window is no longer available."
            )
            return
        filename = (
            AnkiMediaGateway(col).add_image(result.new_image_path)
            if result.new_image_path
            else (result.existing_image_filename or "")
        )
        content = NoteFactory(self._spec).build(
            image_filename=filename,
            structures=result.structures,
            deck_name="",  # the Add window owns the deck
            options=result.options,
            header=result.header,
            back_extra=result.back_extra,
        )
        for name, value in content.fields.items():
            note[name] = value
        # Reflect the new field values into the editor UI; Anki persists the note
        # when the user presses Add.
        self._editor.loadNote()
        count = len(result.structures)
        dialog.finish_saved(f"{_cards(count)} ready — press Add to create.")
