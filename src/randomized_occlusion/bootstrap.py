"""Composition root: wires hooks, the menu, and note-type installation.

This is the only module that reaches out to the live ``mw`` singleton and to
Anki's hook registry. Everything it touches is constructed here and injected
into the collaborators, so the rest of the package has no hidden global state.
"""

from __future__ import annotations

from aqt import gui_hooks, mw
from aqt.qt import QAction, qconnect

from .collection.gateways import AnkiModelGateway
from .config.config_service import AnkiConfigProvider, ConfigService
from .editor.launcher import EditorLauncher
from .notetype.installer import NoteTypeInstaller
from .notetype.spec import DEFAULT_SPEC
from .notetype.templates import TemplateAssembler
from .resources import read_web

_MENU_LABEL = "Randomized Image Occlusion…"


def setup(addon_module: str) -> None:
    """Entry point invoked once from ``__init__`` when running inside Anki."""
    config_service = ConfigService(
        AnkiConfigProvider(mw.addonManager, addon_module)
    )
    launcher = EditorLauncher(mw, config_service)

    _add_menu_action(launcher)
    gui_hooks.profile_did_open.append(
        lambda: _install_notetype(config_service)
    )


def _add_menu_action(launcher: EditorLauncher) -> None:
    action = QAction(_MENU_LABEL, mw)
    qconnect(action.triggered, launcher.open)
    mw.form.menuTools.addAction(action)


def _install_notetype(config_service: ConfigService) -> None:
    col = mw.col
    if col is None:
        return
    assembler = TemplateAssembler(DEFAULT_SPEC, read_web("review/render.js"))
    installer = NoteTypeInstaller(AnkiModelGateway(col), assembler, DEFAULT_SPEC)
    try:
        installer.ensure_installed(config_service.render_config())
    except Exception as exc:  # pragma: no cover - defensive, never block startup
        print(f"[Randomized Image Occlusion] note-type install failed: {exc!r}")
