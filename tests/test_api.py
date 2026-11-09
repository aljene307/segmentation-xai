"""Tests de l'API : endpoints, erreurs en français, chaîne figée identique, sans scikit-learn."""

import json
import shutil
import subprocess
import sys

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app, moteur
from api.moteur import Moteur
from segmentation import config
from segmentation import segments as S

client = TestClient(app)
BON = {"recence_j": 120, "frequence": 1, "montant_rs": 89.9, "part_frais_port": 0.18,
       "mensualites_moy": 2, "articles_par_commande": 1, "delai_livraison_moy_j": 9.5,
       "ecart_prevision_moy_j": -12}


def erreurs(r):
    assert r.status_code == 422
    return {e["champ"]: e["message"] for e in r.json()["erreurs"]}


def test_sante():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["statut"] == "ok" and r.json()["k"] == 5


def test_segments_et_404():
    r = client.get("/segments")
    assert r.status_code == 200 and len(r.json()) == 5
    assert abs(sum(s["part_clients"] for s in r.json()) - 1) < 1e-9
    r = client.get("/segments/9")
    assert r.status_code == 404 and "inconnu" in r.json()["detail"]


def test_regles():
    r = client.get("/regles").json()
    assert r["profondeur"] == 4 and len(r["phrases"]) == 13


def test_affecter_et_expliquer():
    a = client.post("/affecter", json=BON).json()
    e = client.post("/expliquer", json=BON).json()
    assert a == e["segment"]
    for cle in ("distance", "atypique", "frontiere", "deuxieme_segment", "ecretees",
                "loin_du_client_moyen", "loin_du_centre_du_segment", "regle_arbre", "acp", "texte"):
        assert cle in e
    assert len(e["loin_du_client_moyen"]) == 3 and e["texte"].startswith("Client affecté")


def test_valeur_extreme_ecretee_et_signalee():
    e = client.post("/expliquer", json={**BON, "montant_rs": 50000}).json()
    assert [x["variable"] for x in e["ecretees"]] == ["montant_rs"]
    assert e["ecretees"][0]["ramenee_a"] < 2000


def test_delai_zero_accepte():
    assert client.post("/affecter", json={**BON, "delai_livraison_moy_j": 0}).status_code == 200


@pytest.mark.parametrize("modif, champ, attendu", [
    ({"part_frais_port": 1.4}, "part_frais_port", "entre 0 et 1 (1 exclu), reçu 1,4"),
    ({"part_frais_port": 1}, "part_frais_port", "entre 0 et 1"),
    ({"frequence": 0}, "frequence", "entier ≥ 1"),
    ({"frequence": 1.5}, "frequence", "nombre entier attendu"),
    ({"montant_rs": 0}, "montant_rs", "strictement positif"),
    ({"mensualites_moy": 0}, "mensualites_moy", "au moins 1"),
    ({"delai_livraison_moy_j": -1}, "delai_livraison_moy_j", "positif ou nul"),
    ({"recence_j": "abc"}, "recence_j", "nombre attendu"),
])
def test_erreurs_en_francais(modif, champ, attendu):
    assert attendu in erreurs(client.post("/affecter", json={**BON, **modif}))[champ]


def test_valeur_manquante_et_champ_inconnu():
    sans = {k: v for k, v in BON.items() if k != "montant_rs"}
    e = erreurs(client.post("/affecter", json={**sans, "montant": 10}))
    assert e["montant_rs"] == "valeur manquante" and e["montant"].startswith("champ inconnu")


def test_nan_refuse():
    corps = json.dumps(BON).replace("-12", "NaN")
    r = client.post("/affecter", content=corps, headers={"content-type": "application/json"})
    assert "nombre fini" in erreurs(r)["ecart_prevision_moy_j"]


def test_exemples_retrouvent_leur_segment():
    ex = client.get("/exemples").json()
    assert len(ex) == 10 and all("customer" not in json.dumps(x) for x in ex)
    for x in ex:
        assert client.post("/affecter", json=x["client"]).json()["id"] == x["segment_attendu"]


def test_fichier_altere_refuse(tmp_path):
    for f in ("preparation.json", "acp.json", "segments.json", "explication.json",
              "empreintes.json"):
        shutil.copy(config.DOSSIER_MODELES / f, tmp_path / f)
    texte = (tmp_path / "segments.json").read_bytes().replace(b"\n", b"\r\n")
    (tmp_path / "segments.json").write_bytes(texte)  # conversion CRLF, comme au projet 2
    with pytest.raises(RuntimeError, match="altérés"):
        Moteur(tmp_path)


def test_api_sans_scikit_learn_ni_scipy():
    code = ("import sys; sys.path.insert(0, r'%s'); import api.main; "
            "print(any(m.split('.')[0] in ('sklearn', 'scipy', 'matplotlib') for m in sys.modules))"
            % config.RACINE)
    r = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "False"


@pytest.mark.skipif(not config.PROFILS_MISE_DE_COTE.exists(), reason="profils absents")
def test_chaine_figee_identique_sur_les_20_pour_cent():
    """Des valeurs d'origine aux segments : l'API retrouve le segment officiel des 16 201."""
    prof = pd.read_csv(config.PROFILS_MISE_DE_COTE, index_col="customer_unique_id")
    z = pd.read_csv(config.PREPARES_MISE_DE_COTE, index_col="customer_unique_id").loc[prof.index]
    officiel = S.affecter_prepares(z, S.charger()).to_numpy()
    api = moteur.affecter(prof[moteur.variables])
    assert len(api) == 16201 and (api == officiel).all()
