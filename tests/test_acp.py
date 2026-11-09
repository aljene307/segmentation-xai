"""Tests de l'ACP normée : propriétés mathématiques, règles fixées, fichier JSON."""

import json

import numpy as np
import pandas as pd
import pytest

from segmentation import acp as A
from segmentation import config

VARS = ["a", "b", "c", "d"]


def _donnees(n=3000, graine=0):
    """Données standardisées, avec a et b corrélées, c et d indépendantes."""
    rng = np.random.default_rng(graine)
    base = rng.normal(size=n)
    df = pd.DataFrame({"a": base + 0.3 * rng.normal(size=n),
                       "b": base + 0.3 * rng.normal(size=n),
                       "c": rng.normal(size=n), "d": rng.normal(size=n)})
    return (df - df.mean()) / df.std(ddof=0)


@pytest.fixture(scope="module")
def acp():
    return A.apprendre(_donnees(), VARS, 0.70)


def test_valeurs_propres_triees_et_somme_egale_au_nombre_de_variables(acp):
    vp = np.asarray(acp["valeurs_propres"])
    assert np.all(np.diff(vp) <= 1e-12)
    assert vp.sum() == pytest.approx(len(VARS))  # ACP normée : trace = nombre de variables


def test_variance_des_coordonnees_egale_aux_valeurs_propres(acp):
    s = A.projeter(_donnees(), acp)
    assert np.allclose(s.var(ddof=0), acp["valeurs_propres"])
    assert np.allclose(s.mean(), 0, atol=1e-12)


def test_axes_perpendiculaires_et_coordonnees_non_correlees(acp):
    v = np.asarray(acp["vecteurs"])
    assert np.allclose(v.T @ v, np.eye(len(VARS)))
    s = A.projeter(_donnees(), acp)
    c = np.corrcoef(s.to_numpy().T)
    assert np.allclose(c - np.diag(np.diag(c)), 0, atol=1e-10)


def test_avec_tous_les_axes_on_retrouve_les_donnees(acp):
    d = _donnees()
    s = A.projeter(d, acp)
    reconstruit = s.to_numpy() @ np.asarray(acp["vecteurs"]).T + np.asarray(acp["moyenne"])
    assert np.allclose(reconstruit, d.to_numpy())


def test_premier_axe_porte_les_variables_correlees(acp):
    corr = A.correlations(acp)
    assert abs(corr.loc["a", "F1"]) > 0.9 and abs(corr.loc["b", "F1"]) > 0.9


def test_cos2_somme_a_un_sur_tous_les_axes(acp):
    assert np.allclose(A.cos2(acp).sum(axis=1), 1)
    assert np.allclose(A.contributions(acp).sum(axis=0), 100)


def test_convention_de_sens_reproductible(acp):
    v = np.asarray(acp["vecteurs"])
    for j in range(v.shape[1]):
        assert v[np.argmax(np.abs(v[:, j])), j] > 0
    melange = _donnees().sample(frac=1, random_state=3)
    assert np.allclose(A.apprendre(melange, VARS, 0.70)["vecteurs"], v)


def test_projeter_n_apprend_rien(acp):
    avant = json.dumps(acp, sort_keys=True)
    A.projeter(_donnees(graine=9) * 5, acp)
    assert json.dumps(acp, sort_keys=True) == avant


def test_projeter_refuse_une_variable_manquante(acp):
    with pytest.raises(ValueError, match="manquantes"):
        A.projeter(_donnees().drop(columns="c"), acp)


@pytest.mark.parametrize("vp, attendu", [
    ([3.0, 1.5, 1.2, 0.9, 0.5, 0.4, 0.3, 0.2], {"kaiser": 3, "part_cumulee": 3, "retenus": 3}),
    ([2.0, 1.1, 0.95, 0.9, 0.85, 0.8, 0.7, 0.7], {"kaiser": 2, "part_cumulee": 5, "retenus": 5}),
    ([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], {"kaiser": 0, "part_cumulee": 6, "retenus": 6}),
])
def test_regle_du_nombre_d_axes(vp, attendu):
    d = A.nombre_axes(vp, 0.70)
    assert {k: d[k] for k in attendu} == attendu  # Kaiser strict : 1,0 ne compte pas


def test_description_axe_seuil_et_repli():
    d = A.description_axe(pd.Series({"x": 0.8, "y": -0.6, "z": 0.2}), 0.5)
    assert list(d["variables"]) == ["x", "y"]
    assert d["pole_plus"] == ["x élevé", "y faible"]
    repli = A.description_axe(pd.Series({"x": 0.4, "y": -0.45, "z": 0.1}), 0.5)
    assert list(repli["variables"]) == ["y", "x"] and "2 plus fortes" in repli["regle"]


def test_regle_axe_du_temps():
    assert A.axe_du_temps(0.9, -0.86)
    assert not A.axe_du_temps(0.9, 0.3)    # (c) non remplie
    assert not A.axe_du_temps(0.35, -0.6)  # (a) non remplie


def test_json_aller_retour(acp, tmp_path):
    chemin = tmp_path / "acp.json"
    A.sauver(acp, chemin)
    assert A.charger(chemin) == acp
    assert b"\r\n" not in chemin.read_bytes()


@pytest.mark.skipif(not config.ACP.exists() or not config.PREPARES_APPRENTISSAGE.exists(),
                    reason="ACP ou données préparées absentes")
def test_fichier_reel_coherent_avec_les_regles():
    acp = A.charger(config.ACP)
    assert acp["variables"] == config.VARIABLES_PROFIL
    assert acp["part_minimale"] == config.PART_CUMULEE_MINIMALE
    d = A.nombre_axes(acp["valeurs_propres"], config.PART_CUMULEE_MINIMALE)
    assert acp["decision"] == d and d["retenus"] == max(d["kaiser"], d["part_cumulee"])
    z = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    assert acp["clients_apprentissage"] == len(z)
    from segmentation.comparaison import presque_egaux
    assert presque_egaux(A.apprendre(z, config.VARIABLES_PROFIL,
                                     config.PART_CUMULEE_MINIMALE), acp)


def test_cosinus_sous_espaces_invariant_par_rotation_interne():
    rng = np.random.default_rng(1)
    q, _ = np.linalg.qr(rng.normal(size=(6, 3)))
    angle = 0.7
    rotation = np.array([[np.cos(angle), -np.sin(angle), 0],
                         [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    assert np.allclose(A.cosinus_sous_espaces(q, q @ rotation), 1)  # axes tournés, même plan
    autre, _ = np.linalg.qr(rng.normal(size=(6, 3)))
    assert A.cosinus_sous_espaces(q, autre).min() < 0.99


def test_bootstrap_structure_et_reproductibilite(acp):
    blocs = {"F1_F2": [0, 1]}
    b1 = A.stabilite_bootstrap(_donnees(), acp, 5, 42, blocs)
    b2 = A.stabilite_bootstrap(_donnees(), acp, 5, 42, blocs)
    pd.testing.assert_frame_equal(b1, b2)
    assert len(b1) == 5 and b1["cos_F1"].between(0, 1 + 1e-12).all()
    assert (b1["meilleur_F1"] >= b1["cos_F1"] - 1e-12).all()
    assert b1["cos_F1"].min() > 0.99  # F1 (a et b corrélées) est très net : stable
