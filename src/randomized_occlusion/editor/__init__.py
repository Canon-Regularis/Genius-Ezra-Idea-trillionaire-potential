"""The Qt authoring UI for marking structures on an image.

Only :class:`MarkerBridge` (which has no Qt/Anki dependency) is re-exported here.
``dialog`` and ``launcher`` import ``aqt`` and are imported directly by the
composition root, so this package stays importable in headless tests.
"""

from __future__ import annotations

from .bridge import MarkerBridge

__all__ = ["MarkerBridge"]
