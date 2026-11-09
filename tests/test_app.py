"""Tests de l'application : données précalculées (sans identifiant) et affichage de chaque page."""

import json
import re

import pandas as pd
import pytest

from segmentation import config

DONNEES = config.RACINE / "app" / "donnees"
FICHIERS = ["carte.csv", "profils_k.json", "silhouette_k.json", "dendrogrammes.json",
            "exploration.json", "LICENCE.md"]
IDENTIFIANT = re.compile(r"\b[0-9a-f]{32}\b")  # forme des identifiants Olist


def test_fichiers_presents_petits_sans_identifiant_en_lf():
    total = 0
    for f in FICHIERS:
        octets = (DONNEES / f).read_bytes()
        total += len(octets)
        assert b"\r\n" not in octets, f
        assert not IDENTIFIANT.search(octets.decode("utf-8")), f
    assert total < 500 * 1024


def test_carte():
    c = pd.read_csv(DONNEES / "carte.csv")
    assert len(c) == 3000
    assert list(c.columns) == ["F1", "F2"] + [f"segment_k{k}" for k in range(2, 9)]
    for k in range(2, 9):
        assert c[f"segment_k{k}"].between(0, k - 1).all()


def test_profils_et_silhouette_pour_chaque_k():
    p = json.loads((DONNEES / "profils_k.json").read_text(encoding="utf-8"))
    s = json.loads((DONNEES / "silhouette_k.json").read_text(encoding="utf-8"))
    for k in range(2, 9):
        assert len(p[str(k)]) == k and len(s[str(k)]["segments"]) == k
        assert abs(sum(x["part_clients"] for x in p[str(k)]) - 1) < 1e-9
        assert abs(sum(x["part_ca"] for x in p[str(k)]) - 1) < 1e-9


@pytest.mark.skipif(not config.SEGMENTS_APPRENTISSAGE.exists(), reason="données absentes")
def test_carte_k5_segments_officiels():
    from segmentation import acp as A
    from segmentation import partitions as P
    from segmentation import segments as S
    z = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    ids = P.ordre_echantillon(z.index, config.GRAINE)[:3000]
    c = pd.read_csv(DONNEES / "carte.csv")
    assert (c["segment_k5"].to_numpy() == S.segments_apprentissage().loc[ids].to_numpy()).all()
    f = A.projeter(z.loc[ids], A.charger(config.ACP), 2)
    assert (abs(c["F1"].to_numpy() - f["F1"].to_numpy()) < 1e-4).all()


# --- Pages (outil de test de Streamlit, sans navigateur et sans appel réseau) ----------------

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

PAGES = ["accueil", "donnees", "acp", "modelisation", "choix_k", "explicabilite", "api"]


def _page(nom: str) -> AppTest:
    script = (f"import sys\nsys.path[:0] = [{str(config.RACINE)!r}, "
              f"{str(config.RACINE / 'app')!r}]\nfrom vues import {nom}\n{nom}.afficher()\n")
    return AppTest.from_string(script, default_timeout=60)


@pytest.fixture(autouse=True)
def api_injoignable(monkeypatch):
    monkeypatch.setenv("API_URL", "http://127.0.0.1:9")  # aucun appel réel pendant les tests


@pytest.mark.parametrize("nom", PAGES)
def test_chaque_page_s_affiche(nom):
    at = _page(nom).run()
    assert not at.exception, at.exception
    assert at.title[0].value


def test_curseur_k_met_a_jour_la_page():
    at = _page("choix_k").run()
    for k in (2, 5, 8):
        at.slider[0].set_value(k).run()
        assert not at.exception
        texte = " ".join(m.value for m in at.markdown) + " ".join(
            e.value for e in at.success) + " ".join(w.value for w in at.warning)
        assert ("retenu par la règle" in texte) == (k == 5)


def test_api_injoignable_donne_un_message_clair():
    at = _page("explicabilite").run()
    at.button[0].click().run()  # « Expliquer ce client »
    assert not at.exception
    assert any("injoignable" in e.value for e in at.error)


def test_application_complete_demarre():
    at = AppTest.from_file(str(config.RACINE / "app" / "app.py"), default_timeout=60).run()
    assert not at.exception


def test_application_sans_scikit_learn_ni_scipy():
    import subprocess
    import sys
    code = ("import sys; sys.path[:0] = [%r, %r]; "
            "from vues import accueil, acp, api, choix_k, donnees, explicabilite, modelisation; "
            "print(any(m.split('.')[0] in ('sklearn', 'scipy', 'matplotlib') for m in sys.modules))"
            % (str(config.RACINE), str(config.RACINE / "app")))
    r = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == "False"


def test_dependances_de_l_application():
    lignes = (config.RACINE / "app" / "requirements.txt").read_text(encoding="utf-8").splitlines()
    paquets = {l.split("==")[0] for l in lignes if l and not l.startswith("#")}
    assert {"streamlit", "numpy", "pandas", "requests"} <= paquets
    assert not paquets & {"scikit-learn", "scipy", "matplotlib"}
    assert all("==" in l for l in lignes if l and not l.startswith("#"))  # versions épinglées
