"""Tests de la préparation : règle du log, écrêtage, standardisation, fichier JSON."""

import json

import numpy as np
import pandas as pd
import pytest

from segmentation import config
from segmentation import preparation as prepa

RNG = np.random.default_rng(0)  # pour les données ponctuelles d'un seul test
N = 2000


def _donnees():
    """Toujours les mêmes données (graine fixée à chaque appel)."""
    RNG = np.random.default_rng(0)
    return pd.DataFrame({
        "etire": RNG.lognormal(3, 1.2, N),          # positive, très asymétrique → log
        "symetrique": RNG.normal(50, 10, N),        # asymétrie < 1 → pas de log
        "proportion": RNG.beta(1, 6, N),            # bornée → hors règle
        "signe": RNG.exponential(10, N) - 15,       # valeurs négatives → hors règle
    })


VARS = ["etire", "symetrique", "proportion", "signe"]


@pytest.fixture(scope="module")
def prep():
    return prepa.apprendre(_donnees(), VARS, ["proportion"], 1.0, (0.005, 0.995))


def test_regle_du_log(prep):
    p = prep["parametres"]
    assert p["etire"]["log"] is True
    assert p["symetrique"]["log"] is False and "asymétrie" in p["symetrique"]["raison"]
    assert p["proportion"]["log"] is False and "bornée" in p["proportion"]["raison"]
    assert p["signe"]["log"] is False and "négatives" in p["signe"]["raison"]


def test_pas_de_log_si_le_log_ne_reduit_pas():
    # Variable positive étirée vers la GAUCHE : le log l'aggrave.
    x = pd.DataFrame({"v": 1000 - RNG.lognormal(3, 1.0, N).clip(max=999)})
    p = prepa.apprendre(x, ["v"], [], 1.0, (0.005, 0.995))["parametres"]["v"]
    assert abs(p["asymetrie_brute"]) > 1 and p["log"] is False


def test_apprentissage_moyenne_0_ecart_type_1(prep):
    z = prepa.appliquer(_donnees(), prep)
    assert np.allclose(z.mean(), 0, atol=1e-12)
    assert np.allclose(z.std(ddof=0), 1, atol=1e-12)


def test_ecretage_aux_seuils_appris(prep):
    d = _donnees()
    t = prepa.transformer(d, prep)
    p = prep["parametres"]["etire"]
    assert t["etire"].quantile(0.005) == pytest.approx(p["bas"])
    extreme = pd.DataFrame({v: [d[v].max() * 1000 if v != "proportion" else 1.0] for v in VARS})
    z = prepa.appliquer(extreme, prep)
    attendu = (p["haut"] - p["moyenne"]) / p["ecart_type"]
    assert z.loc[0, "etire"] == pytest.approx(attendu)  # ramené au seuil haut
    assert prepa.indicateur_ecretage(extreme, prep).loc[0, "ecrete"]


def test_appliquer_n_apprend_rien(prep):
    avant = json.dumps(prep, sort_keys=True)
    autres = _donnees() * 3
    prepa.appliquer(autres, prep)
    assert json.dumps(prep, sort_keys=True) == avant


def test_indicateur_liste_les_variables(prep):
    d = _donnees().iloc[[0]].copy()
    d["etire"] = 1e9
    d["signe"] = 1e6
    ind = prepa.indicateur_ecretage(d, prep).iloc[0]
    assert ind["ecrete"] and ind["variables_ecretees"] == "etire;signe"


def test_json_aller_retour_identique(prep, tmp_path):
    chemin = tmp_path / "prep.json"
    prepa.sauver(prep, chemin)
    relu = prepa.charger(chemin)
    assert relu == prep
    d = _donnees()
    pd.testing.assert_frame_equal(prepa.appliquer(d, relu), prepa.appliquer(d, prep))
    assert b"\r\n" not in chemin.read_bytes()  # LF seulement


def test_refuse_client_incomplet_ou_impossible(prep):
    d = _donnees().iloc[[0]]
    with pytest.raises(ValueError, match="manquantes"):
        prepa.appliquer(d.drop(columns="signe"), prep)
    with pytest.raises(ValueError, match="manquantes"):
        prepa.appliquer(d.assign(symetrique=np.nan), prep)
    with pytest.raises(ValueError, match="négative"):
        prepa.appliquer(d.assign(etire=-5.0), prep)


def test_seuils_en_unites(prep):
    u = prepa.seuils_en_unites(prep)
    d = _donnees()
    assert u["etire"][1] == pytest.approx(np.expm1(np.log1p(d["etire"]).quantile(0.995)))
    assert u["signe"][0] == pytest.approx(d["signe"].quantile(0.005))


@pytest.mark.skipif(not config.PREPARATION.exists() or not config.PROFILS_APPRENTISSAGE.exists(),
                    reason="préparation ou profils absents")
def test_fichier_reel_coherent_avec_les_regles():
    prep = prepa.charger(config.PREPARATION)
    assert prep["variables"] == config.VARIABLES_PROFIL
    assert tuple(prep["centiles"]) == config.CENTILES_ECRETAGE
    logs = {v for v, p in prep["parametres"].items() if p["log"]}
    assert logs == {"frequence", "montant_rs", "mensualites_moy",
                    "articles_par_commande", "delai_livraison_moy_j"}
    app = pd.read_csv(config.PROFILS_APPRENTISSAGE, index_col="customer_unique_id")
    assert prep["clients_apprentissage"] == len(app)
    reappris = prepa.apprendre(app, config.VARIABLES_PROFIL, config.VARIABLES_BORNEES,
                               config.SEUIL_ASYMETRIE_LOG, config.CENTILES_ECRETAGE)
    assert reappris == prep  # appris sur les 80 % exactement
