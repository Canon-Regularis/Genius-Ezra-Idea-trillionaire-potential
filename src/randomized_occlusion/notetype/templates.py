"""Assembles the note type's HTML/CSS from the spec, config, and reviewer JS.

The ``TemplateAssembler`` has a single responsibility: turn a
:class:`NoteTypeSpec` plus a :class:`RenderConfig` plus the renderer JavaScript
into the three strings Anki stores on a note type (front HTML, back HTML, CSS).
It knows nothing about the collection or how the note type is installed.
"""

from __future__ import annotations

import hashlib
import re
from textwrap import dedent

from ..config.render_config import RenderConfig
from .spec import NoteTypeSpec

#: Bump when the template *skeleton* (not the JS/CSS) changes, to force updates.
TEMPLATE_VERSION = 1

_FINGERPRINT_RE = re.compile(r"ro-fingerprint:([0-9a-f]+)")


def extract_fingerprint(css: str) -> str | None:
    """Recover the fingerprint embedded in an installed note type's CSS."""
    match = _FINGERPRINT_RE.search(css or "")
    return match.group(1) if match else None


def _script_safe(text: str) -> str:
    """Neutralise any ``</`` so embedded text can't terminate a ``<script>``.

    ``<\\/`` is equivalent to ``</`` both inside a JSON string (``\\/`` is a valid
    JSON escape for ``/``) and inside our JavaScript, so this is safe for every
    payload we embed in a ``<script>`` element — the renderer JS and the config
    JSON alike (the latter carries user-editable values such as ``prompt_text``).
    """
    return text.replace("</", "<\\/")


class TemplateAssembler:
    def __init__(self, spec: NoteTypeSpec, render_js: str) -> None:
        self._spec = spec
        self._render_js = _script_safe(render_js)

    # -- public API ------------------------------------------------------------

    def front(self, render_config: RenderConfig) -> str:
        s = self._spec
        return dedent(
            """\
            <div id="ro-root" class="ro-root">
              {{{{#{header}}}}}<div class="ro-header">{{{{{header}}}}}</div>{{{{/{header}}}}}
              <div id="ro-stage" class="ro-stage">
                {{{{{image}}}}}
                <svg id="ro-overlay" class="ro-overlay" xmlns="http://www.w3.org/2000/svg"></svg>
              </div>
              <div id="ro-ordinal" class="ro-hidden">{{{{cloze:{cloze}}}}}</div>
              <script id="ro-data" type="application/json">{{{{{structures}}}}}</script>
              <script id="ro-config" type="application/json">{config}</script>
              <script>{render_js}</script>
            </div>
            """
        ).format(
            header=s.header_field,
            image=s.image_field,
            cloze=s.cloze_field,
            structures=s.structures_field,
            config=_script_safe(render_config.behaviour_json()),
            render_js=self._render_js,
        )

    def back(self) -> str:
        s = self._spec
        return dedent(
            """\
            {{{{FrontSide}}}}
            <div id="ro-answer" class="ro-answer" aria-hidden="true"></div>
            {{{{#{extra}}}}}<div class="ro-extra">{{{{{extra}}}}}</div>{{{{/{extra}}}}}
            """
        ).format(extra=s.back_extra_field)

    def css(self, render_config: RenderConfig) -> str:
        fingerprint = self.fingerprint(render_config)
        return f"/* ro-fingerprint:{fingerprint} */\n" + self._css_body(render_config)

    def _css_body(self, render_config: RenderConfig) -> str:
        variables = "".join(
            f"  {name}: {value};\n"
            for name, value in render_config.css_variables().items()
        )
        return dedent(
            """\
            .card {{
              font-family: arial, sans-serif;
              font-size: 18px;
              text-align: center;
              color: black;
              background-color: white;
            }}
            .ro-root {{
            {variables}}}
            .ro-header {{ font-weight: 600; margin-bottom: 10px; }}
            .ro-stage {{ position: relative; display: inline-block; max-width: 100%; line-height: 0; }}
            .ro-stage img {{ display: block; max-width: 100%; height: auto; }}
            .ro-overlay {{
              position: absolute; left: 0; top: 0; width: 100%; height: 100%;
              pointer-events: none; overflow: visible;
            }}
            /* Kept in the DOM (so JS can read them) but visually suppressed. */
            .ro-hidden, .ro-answer {{
              position: absolute; width: 0; height: 0;
              overflow: hidden; opacity: 0;
            }}
            .ro-box-rect {{ fill: var(--ro-box-fill); stroke: var(--ro-accent); stroke-width: 2; }}
            .ro-box-text {{
              fill: var(--ro-box-text); font-size: 18px; font-weight: 700;
              font-family: arial, sans-serif;
            }}
            .ro-arrow {{ stroke: var(--ro-accent); stroke-width: 2.5; fill: none; }}
            .ro-arrowhead path {{ fill: var(--ro-accent); stroke: none; }}
            .ro-dot {{ fill: var(--ro-dot); stroke: #ffffff; stroke-width: 1.5; }}
            .ro-extra {{ margin-top: 14px; line-height: normal; font-size: 16px; }}
            """
        ).format(variables=variables)

    def fingerprint(self, render_config: RenderConfig) -> str:
        """A short hash over everything that affects the rendered card.

        Hashes the *actual* assembled front, back, and CSS body (which already
        embed the renderer JS, the config, and the colour variables), so any
        change — including to the HTML/CSS skeleton — is detected automatically
        and the installer refreshes already-installed note types. The CSS body
        is hashed *without* its own fingerprint comment to avoid self-reference.
        """
        payload = "\n".join(
            [
                str(TEMPLATE_VERSION),
                self.front(render_config),
                self.back(),
                self._css_body(render_config),
            ]
        )
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
