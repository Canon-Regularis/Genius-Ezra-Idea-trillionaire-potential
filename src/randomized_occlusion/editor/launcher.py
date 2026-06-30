"""Opens the editor dialog, keeping a reference so Qt does not garbage-collect it."""

from __future__ import annotations

from typing import Any

from aqt.utils import showInfo

from ..config.config_service import ConfigService
from .dialog import MarkerDialog


class EditorLauncher:
    def __init__(self, main_window: Any, config_service: ConfigService) -> None:
        self._mw = main_window
        self._config = config_service
        self._dialog: MarkerDialog | None = None

    def open(self) -> None:
        if self._mw.col is None:
            showInfo("Please open a collection first.")
            return
        dialog = MarkerDialog(self._mw, self._config)
        # Hold a reference; a local would be collected and close the window.
        self._dialog = dialog
        dialog.show()
