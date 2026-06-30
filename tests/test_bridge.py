from __future__ import annotations

from randomized_occlusion.editor.bridge import MarkerBridge


class Spy:
    def __init__(self):
        self.ready = 0
        self.counts = []

    def on_ready(self):
        self.ready += 1

    def on_count(self, n):
        self.counts.append(n)


def _bridge(spy):
    return MarkerBridge(on_ready=spy.on_ready, on_count=spy.on_count)


def test_ready_message_invokes_callback():
    spy = Spy()
    _bridge(spy).handle("ro:ready")
    assert spy.ready == 1


def test_count_message_parses_integer():
    spy = Spy()
    _bridge(spy).handle("ro:count:3")
    assert spy.counts == [3]


def test_count_message_with_garbage_defaults_to_zero():
    spy = Spy()
    _bridge(spy).handle("ro:count:abc")
    assert spy.counts == [0]


def test_foreign_messages_are_ignored():
    spy = Spy()
    bridge = _bridge(spy)
    bridge.handle("anki:something")
    bridge.handle("")
    assert spy.ready == 0 and spy.counts == []
