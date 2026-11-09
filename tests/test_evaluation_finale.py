"""Tests de l'évaluation finale sur des données inventées (la vraie ne se lance qu'une fois)."""

import numpy as np
import pandas as pd
import pytest

from segmentation import evaluation_finale as E
from segmentation import explication as X

VARS = ["montant_rs", "ecart_prevision_moy_j"]


def _groupe(n=2000, graine=0):
    rng = np.random.default_rng(graine)
    ids = [f"c{graine}_{i:05d}" for i in range(n)]
    centres = np.array([[0, 0], [4, 0], [0, 4], [4, 4], [8, 8]], dtype=float)
    seg = rng.choice(5, size=n, p=[.4, .3, .15, .1, .05])
    z = pd.DataFrame(centres[seg] + rng.normal(size=(n, 2)), index=ids, columns=VARS)
    prof = z.copy()
    prof["ecart_prevision_moy_j"] = np.where(seg == 2, 5.0, -10.0) + rng.normal(size=n)
    notes = pd.DataFrame({"satisfait": np.where(seg == 2, rng.random(n) < .5,
                                                np.where(seg == 3, rng.random(n) < .6,
                                                         rng.random(n) < .85))}, index=ids)
    notes = notes.iloc[: int(0.99 * n)]
    pv = pd.Series(rng.random(n) < .15, index=ids)
    seg = pd.Series(seg, index=ids)
    return z, prof, seg, notes, pv, centres


def _mesures(graine):
    z, prof, seg, notes, pv, centres = _groupe(graine=graine)
    seuils = X.seuils_atypiques(z[VARS].to_numpy(), seg.to_numpy(), centres)
    arbre = X.apprendre_arbre(prof[VARS], seg, 3, 20, 42)
    return E.mesurer(z, prof, seg, notes, pv, centres, seuils, arbre, list(z.index[:500]), VARS)


def test_mesurer_structure_et_bornes():
    m = _mesures(0)
    assert m["clients"] == 2000 and len(m["parts"]) == 5
    assert sum(m["parts"]) == pytest.approx(1)
    assert m["sans_avis"] == pytest.approx(0.01)
    assert 0 <= m["satisfaits"] <= 1 and m["ordre_satisfaction"][-1] == 2
    assert m["ecart_retard"] > 0.2


def test_verdicts_douze_attentes_et_seuils():
    r, m = _mesures(0), _mesures(1)
    v = E.verdicts(r, m)
    assert [x["code"] for x in v] == [f"E{i}" for i in range(1, 13)]
    assert {x["statut"] for x in v if x["code"] in ("E3", "E4", "E5")} == {"déjà observé"}
    # Un écart de part trop grand fait échouer E1.
    m2 = dict(m, parts=[m["parts"][0] + 0.02] + m["parts"][1:])
    assert not E.verdicts(r, m2)[0]["atteinte"]
    # E9 : S2 doit être dernier.
    m3 = dict(m, ordre_satisfaction=[0, 1, 4, 2, 3])
    assert not E.verdicts(r, m3)[8]["atteinte"]
    # E11 : seuil de 40 points inclus.
    m4 = dict(m, ecart_retard=0.40)
    assert E.verdicts(r, m4)[10]["atteinte"]


def test_fichiers_absents_message_clair(tmp_path):
    present = tmp_path / "present.csv"
    present.write_text("x")
    E.exiger_fichiers([present])  # rien ne manque : pas d'arrêt
    with pytest.raises(SystemExit) as e:
        E.exiger_fichiers([present, tmp_path / "absent.csv"])
    message = str(e.value)
    assert "absent.csv" in message and "present.csv" not in message
    assert "étapes 1 à 12 du README" in message


def test_le_script_verifie_les_fichiers_avant_de_les_lire():
    from segmentation import config
    texte = (config.RACINE / "scripts" / "evaluation_finale.py").read_text(encoding="utf-8")
    verif = texte.index("E.exiger_fichiers(")
    assert verif < texte.index("pd.read_csv(") and verif < texte.index("charger_tables(")
    assert texte.index("REFUS") < verif  # le verrou de l'ouverture unique passe avant
