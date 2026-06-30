from __future__ import annotations

import pytest

from randomized_occlusion.domain.geometry import NormalizedPoint
from randomized_occlusion.domain.structure import Structure
from randomized_occlusion.domain.structure_set import StructureSet


def _s(ordinal, label, x=0.5, y=0.5):
    return Structure(ordinal=ordinal, target=NormalizedPoint(x, y), label=label)


def test_requires_at_least_one_structure():
    with pytest.raises(ValueError):
        StructureSet(structures=())


def test_rejects_ordinal_gaps():
    with pytest.raises(ValueError):
        StructureSet(structures=(_s(1, "a"), _s(3, "c")))


def test_rejects_duplicate_ordinals():
    with pytest.raises(ValueError):
        StructureSet(structures=(_s(1, "a"), _s(1, "b")))


def test_from_unordered_assigns_contiguous_ordinals():
    s = StructureSet.from_unordered([_s(99, "a"), _s(7, "b"), _s(3, "c")])
    assert [x.ordinal for x in s.ordered] == [1, 2, 3]
    assert [x.label for x in s.ordered] == ["a", "b", "c"]


def test_cloze_field_format():
    s = StructureSet.from_unordered([_s(1, "a"), _s(1, "b")])
    assert s.cloze_field() == "{{c1::1}}{{c2::2}}"


def test_base64_roundtrip_preserves_unicode_labels():
    original = StructureSet.from_unordered(
        [_s(1, "Aorta"), _s(2, "Schlüsselbein"), _s(3, "上腕骨")]
    )
    restored = StructureSet.from_base64(original.to_base64())
    assert restored == original


def test_base64_is_ascii_safe():
    s = StructureSet.from_unordered([_s(1, "<script>alert(1)</script>")])
    payload = s.to_base64()
    assert payload.isascii()
    assert "<" not in payload and ">" not in payload
    assert StructureSet.from_base64(payload) == s
