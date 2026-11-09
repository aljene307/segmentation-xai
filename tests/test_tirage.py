"""Tests du tirage des clients mis de côté."""

import json
import random

import pandas as pd
import pytest

from segmentation import config
from segmentation.tirage import empreinte, separer

IDS = [f"client_{i:05d}" for i in range(1000)]


def test_groupes_disjoints_et_complets():
    app, cote = separer(IDS, 0.2, 42)
    assert len(cote) == 200 and len(app) == 800
    assert not set(app) & set(cote)
    assert set(app) | set(cote) == set(IDS)


def test_independant_de_l_ordre_des_lignes():
    melanges = IDS[:]
    random.Random(7).shuffle(melanges)
    assert separer(melanges, 0.2, 42) == separer(IDS, 0.2, 42)


def test_doublons_ignores():
    assert separer(IDS + IDS[:10], 0.2, 42) == separer(IDS, 0.2, 42)


def test_la_graine_change_le_tirage():
    assert separer(IDS, 0.2, 42)[1] != separer(IDS, 0.2, 43)[1]


def test_empreinte_independante_de_l_ordre():
    assert empreinte(["b", "a"]) == empreinte(["a", "b"]) != empreinte(["a", "c"])


@pytest.mark.skipif(not config.PROFILS_MISE_DE_COTE.exists(),
                    reason="profils absents : lancer construire_profil.py")
def test_tirage_reel_identique_a_l_empreinte_versionnee():
    ref = json.loads(config.EMPREINTE_TIRAGE.read_text(encoding="utf-8"))
    app = pd.read_csv(config.PROFILS_APPRENTISSAGE, usecols=["customer_unique_id"])
    cote = pd.read_csv(config.PROFILS_MISE_DE_COTE, usecols=["customer_unique_id"])
    assert len(app) == ref["clients_apprentissage"]
    assert len(cote) == ref["clients_mise_de_cote"]
    assert empreinte(cote["customer_unique_id"]) == ref["sha256_mise_de_cote"]
    assert not set(app["customer_unique_id"]) & set(cote["customer_unique_id"])
