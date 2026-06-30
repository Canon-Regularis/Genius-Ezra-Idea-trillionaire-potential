from __future__ import annotations

from randomized_occlusion.config.defaults import DEFAULT_CONFIG
from randomized_occlusion.config.render_config import RenderConfig
from randomized_occlusion.notetype.installer import InstallResult, NoteTypeInstaller
from randomized_occlusion.notetype.spec import DEFAULT_SPEC
from randomized_occlusion.notetype.templates import TemplateAssembler


class FakeModelGateway:
    """In-memory ModelGateway, Liskov-substitutable for the real one."""

    def __init__(self):
        self.store = {}
        self.created = []
        self.updated = []

    def find(self, name):
        return self.store.get(name)

    def create_cloze_notetype(self, *, name, fields, sort_index, template_name, front, back, css):
        self.store[name] = {
            "name": name,
            "type": 1,
            "flds": [{"name": f} for f in fields],
            "tmpls": [{"name": template_name, "qfmt": front, "afmt": back}],
            "css": css,
            "sortf": sort_index,
        }
        self.created.append(name)

    def update_templates(self, notetype, *, front, back, css):
        notetype["tmpls"][0]["qfmt"] = front
        notetype["tmpls"][0]["afmt"] = back
        notetype["css"] = css
        self.updated.append(notetype["name"])


def _installer(gateway):
    assembler = TemplateAssembler(DEFAULT_SPEC, "/* render */")
    return NoteTypeInstaller(gateway, assembler, DEFAULT_SPEC)


def _rc(**overrides):
    return RenderConfig.from_mapping({**DEFAULT_CONFIG, **overrides})


def test_creates_when_absent():
    gw = FakeModelGateway()
    result = _installer(gw).ensure_installed(_rc())
    assert result is InstallResult.CREATED
    assert gw.created == [DEFAULT_SPEC.name]
    assert DEFAULT_SPEC.name in gw.store


def test_unchanged_when_fingerprint_matches():
    gw = FakeModelGateway()
    installer = _installer(gw)
    installer.ensure_installed(_rc())
    result = installer.ensure_installed(_rc())
    assert result is InstallResult.UNCHANGED
    assert gw.updated == []


def test_updates_when_config_changes():
    gw = FakeModelGateway()
    installer = _installer(gw)
    installer.ensure_installed(_rc())
    result = installer.ensure_installed(_rc(accent_color="#000000"))
    assert result is InstallResult.UPDATED
    assert gw.updated == [DEFAULT_SPEC.name]
    assert "--ro-accent: #000000;" in gw.store[DEFAULT_SPEC.name]["css"]


def test_creates_a_cloze_notetype():
    gw = FakeModelGateway()
    _installer(gw).ensure_installed(_rc())
    assert gw.store[DEFAULT_SPEC.name]["type"] == 1
