"""Tests de l'explicabilité : profils, arbre (règle, prédiction, phrases), explication d'un client."""

import json

import numpy as np
import pandas as pd
import pytest
from sklearn.tree import DecisionTreeClassifier

from segmentation import config
from segmentation import explication as X


def test_indices_profil_rapport_et_difference():
    prof = pd.DataFrame({"montant_rs": [10.0, 30.0, 20.0, 40.0],
                         "ecart_prevision_moy_j": [-10.0, -14.0, 0.0, 4.0]})
    seg = pd.Series([0, 0, 1, 1])
    ip = X.indices_profil(prof, seg, ["montant_rs", "ecart_prevision_moy_j"])
    assert ip.loc[0, "montant_rs"] == pytest.approx(20 / 25)       # rapport
    assert ip.loc[1, "ecart_prevision_moy_j"] == pytest.approx(2 - (-5))  # différence en jours
    assert X.part_ca(prof, seg).tolist() == pytest.approx([40.0, 60.0])


@pytest.mark.parametrize("f3, f4, attendu", [
    (0.90, 0.99, 3), (0.8379, 0.8742, 4), (0.85, 0.875, 3), (0.85, 0.88, 4)])
def test_regle_de_profondeur(f3, f4, attendu):
    assert X.choisir_profondeur(f3, f4) == attendu


def _donnees_arbre():
    rng = np.random.default_rng(0)
    x = pd.DataFrame({"montant_rs": rng.uniform(0, 300, 2000),
                      "delai_livraison_moy_j": rng.uniform(0, 40, 2000)})
    y = pd.Series(np.where(x["delai_livraison_moy_j"] > 20, 2,
                           np.where(x["montant_rs"] > 100, 0, 1)))
    return x, y


def test_prediction_sans_scikit_learn_identique():
    x, y = _donnees_arbre()
    arbre = X.apprendre_arbre(x, y, 3, 20, 42)
    m = DecisionTreeClassifier(max_depth=3, min_samples_leaf=20, random_state=42).fit(x.to_numpy(), y)
    assert (X.predire_arbre(arbre, x) == m.predict(x.to_numpy())).all()
    assert (X.predire_arbre(arbre, x) == y.to_numpy()).mean() > 0.98


def test_regles_intervalles_et_phrases():
    x, y = _donnees_arbre()
    arbre = X.apprendre_arbre(x, y, 2, 20, 42)
    r = X.regles(arbre)
    assert sum(regle["clients"] for regle in r) == len(x)
    for regle in r:
        for bas, haut in regle["conditions"].values():
            assert bas is None or haut is None or bas < haut
    ph = X.phrase(r[0], {0: "A", 1: "B", 2: "C"})
    assert ph.startswith("Si ") and "clients de cette règle" in ph
    assert (" R$" in ph) or ("jours" in ph)


def test_condition_en_mots():
    assert X.condition_en_mots("montant_rs", None, 66.99) == "le montant est au plus de 66,99 R$"
    assert X.condition_en_mots("part_frais_port", 0.2, None) == \
        "la part des frais de port est supérieure à 0,20"
    assert X.condition_en_mots("delai_livraison_moy_j", 2, 13.25).startswith(
        "le délai de livraison moyen est entre 2,0 jours et 13,2")


def test_diagnostic_frontiere_et_atypique():
    centres = np.array([[0.0, 0.0], [10.0, 0.0]])
    z = np.array([[1.0, 0.0], [4.8, 0.0], [0.0, 3.0]])
    d = X.diagnostic(z, centres, seuils=[2.0, 2.0])
    assert d["segment"].tolist() == [0, 0, 0]
    assert d["frontiere"].tolist() == [False, True, False]   # 4,8 / 5,2 ≥ 0,90
    assert d["atypique"].tolist() == [False, True, True]     # distances 1 ; 4,8 ; 3 contre 2


def test_seuils_atypiques_95e_centile():
    z = np.arange(100, dtype=float)[:, None]
    s = X.seuils_atypiques(z, np.zeros(100, dtype=int), np.array([[0.0]]))
    assert s[0] == pytest.approx(np.quantile(np.arange(100), 0.95))


def test_principales_variables_et_explication():
    p = X.principales(np.array([0.1, -3.0, 2.0, 0.0]), ["a", "b", "c", "d"])
    assert [v for v, _, _ in p] == ["b", "c", "a"]
    assert sum(part for _, part, _ in p) <= 1 + 1e-12 and p[0][2] < 0
    variables = ["montant_rs", "delai_livraison_moy_j"]
    e = X.expliquer(np.array([2.0, 0.1]), pd.Series({"montant_rs": 500.0,
                                                    "delai_livraison_moy_j": 12.0}),
                    np.array([[1.5, 0.0], [-1.0, 0.0]]), [1.0, 1.0], variables,
                    {"montant_rs": 140.0, "delai_livraison_moy_j": 13.0},
                    {0: {"montant_rs": 130.0, "delai_livraison_moy_j": 9.0},
                     1: {"montant_rs": 35.0, "delai_livraison_moy_j": 10.0}})
    assert e["segment"] == 0 and not e["atypique"] and not e["frontiere"]
    assert e["loin_du_client_moyen"][0]["variable"] == "montant_rs"
    assert e["loin_du_client_moyen"][0]["sens"] == "au-dessus"


@pytest.mark.skipif(not (config.DOSSIER_MODELES / "explication.json").exists(),
                    reason="explication non calculée")
def test_fichier_explication_reel():
    chemin = config.DOSSIER_MODELES / "explication.json"
    e = json.loads(chemin.read_text(encoding="utf-8"))
    assert e["variables"] == config.VARIABLES_PROFIL
    assert len(e["seuils_atypiques"]) == config.K_RETENU
    assert e["arbre"]["profondeur"] in (3, 4) and e["arbre"]["feuille_min"] == 649
    assert len(e["regles"]) == sum(1 for g in e["arbre"]["gauche"] if g == -1)
    assert b"\r\n" not in chemin.read_bytes()


def test_variables_entieres_en_forme_naturelle():
    assert X.condition_en_mots("frequence", 1.5, None) == "le client a au moins 2 commandes"
    assert X.condition_en_mots("frequence", None, 1.5) == "le client a au plus 1 commande"
    assert X.condition_en_mots("frequence", 1.5, 2.5) == "le client a exactement 2 commandes"
    assert X.condition_en_mots("frequence", 1.5, 4.5) == "le client a entre 2 et 4 commandes"
