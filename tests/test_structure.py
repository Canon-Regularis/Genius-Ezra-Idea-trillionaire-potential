from __future__ import annotations

import pytest

from randomized_occlusion.domain.geometry import NormalizedPoint
from randomized_occlusion.domain.structure import Structure


def _structure(**kwargs):
    defaults = dict(ordinal=1, target=NormalizedPoint(0.3, 0.4), label="Aorta")
    defaults.update(kwargs)
    return Structure(**defaults)


def test_valid_structure_roundtrips_through_dict():
    structure = _structure()
    assert Structure.from_dict(structure.to_dict()) == structure


def test_to_dict_uses_compact_keys():
    assert _structure().to_dict() == {"ord": 1, "x": 0.3, "y": 0.4, "label": "Aorta"}


def test_rejects_non_positive_ordinal():
    with pytest.raises(ValueError):
        _structure(ordinal=0)


@pytest.mark.parametrize("label", ["", "   "])
def test_rejects_blank_label(label):
    with pytest.raises(ValueError):
        _structure(label=label)
