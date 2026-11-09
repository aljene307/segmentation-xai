"""Tests de l'affectation officielle (centre le plus proche de models/segments.json)."""

import pandas as pd
import pytest

from segmentation import config
from segmentation import segments as S


def _segments():
    return {"version": 1, "variables": ["a", "b"],
            "segments": [{"id": 0, "centre": [0.0, 0.0]}, {"id": 1, "centre": [10.0, 0.0]}]}


def test_affectation_au_centre_le_plus_proche():
    z = pd.DataFrame({"a": [1.0, 9.0, 4.9, 5.1], "b": [0.0, 1.0, 0.0, 0.0]},
                     index=["c1", "c2", "c3", "c4"])
    assert S.affecter_prepares(z, _segments()).tolist() == [0, 1, 0, 1]


def test_colonnes_supplementaires_ignorees_et_manquantes_refusees():
    z = pd.DataFrame({"b": [0.0], "a": [9.0], "autre": [123.0]})
    assert S.affecter_prepares(z, _segments()).tolist() == [1]
    with pytest.raises(ValueError, match="manquantes"):
        S.affecter_prepares(z.drop(columns="a"), _segments())


@pytest.mark.skipif(not config.SEGMENTS_APPRENTISSAGE.exists()
                    or not config.PREPARES_APPRENTISSAGE.exists(),
                    reason="segments officiels ou données préparées absents")
def test_segments_officiels_reels():
    seg = S.charger()
    z = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    officiel = S.segments_apprentissage().loc[z.index]
    assert (S.affecter_prepares(z, seg) == officiel).all()
    sauve = pd.read_csv(config.SEGMENTS_APPRENTISSAGE, index_col="customer_unique_id")
    assert int((sauve["segment"] != sauve["segment_kmeans"]).sum()) == 34
    assert [s["clients"] for s in seg["segments"]] == \
        officiel.value_counts().sort_index().tolist()
