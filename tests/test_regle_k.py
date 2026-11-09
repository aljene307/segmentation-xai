"""Tests de la règle de choix de k, sur des tableaux construits à la main."""

import pandas as pd

from segmentation import regle_k as R


def _table(**colonnes):
    base = {"plus_petit_pct": [10.0] * 4, "ari_boot_moyen": [0.9] * 4,
            "jaccard_min": [0.9] * 4, "silhouette": [0.2] * 4,
            "calinski_harabasz": [100.0] * 4, "davies_bouldin": [1.0] * 4}
    base.update(colonnes)
    return pd.DataFrame(base, index=pd.Index([2, 3, 4, 5], name="k"))


def test_admissibilite_seuils_inclus():
    t = _table(plus_petit_pct=[2.0, 1.99, 10, 10], ari_boot_moyen=[0.8, 0.9, 0.79, 0.9],
               jaccard_min=[0.6, 0.9, 0.9, 0.59])
    a = R.admissibilite(t)
    assert a["admissible"].tolist() == [True, False, False, False]


def test_somme_des_rangs_et_sens_des_indices():
    t = _table(silhouette=[0.10, 0.30, 0.20, 0.25],        # rangs 4, 1, 3, 2
               calinski_harabasz=[50, 60, 300, 200],       # rangs 4, 3, 1, 2
               davies_bouldin=[2.0, 1.5, 1.2, 1.0])        # rangs 4, 3, 2, 1
    r = R.rangs(t)
    assert r["somme"].tolist() == [12, 7, 6, 5]
    assert R.choisir_k(t)["k"] == 5


def test_egalite_donne_le_plus_petit_k():
    t = _table(silhouette=[0.1, 0.3, 0.2, 0.25], calinski_harabasz=[50, 300, 60, 200],
               davies_bouldin=[2.0, 1.5, 1.0, 1.2])
    # sommes : k2 = 12, k3 = 1+1+3 = 5, k4 = 3+3+1 = 7, k5 = 2+2+2 = 6
    assert R.choisir_k(t)["k"] == 3
    t2 = _table(silhouette=[0.1, 0.3, 0.2, 0.1], calinski_harabasz=[50, 60, 300, 50],
                davies_bouldin=[2.0, 1.0, 1.5, 2.0])
    # k3 = 1+2+1 = 4 ; k4 = 2+1+2 = 5 ; égalité absente ici, puis cas d'égalité :
    t2.loc[4, ["silhouette", "calinski_harabasz", "davies_bouldin"]] = [0.3, 60, 1.0]
    assert R.choisir_k(t2)["k"] == 3


def test_seuls_les_admissibles_sont_classes():
    t = _table(silhouette=[0.1, 0.9, 0.2, 0.3], ari_boot_moyen=[0.9, 0.5, 0.9, 0.9])
    res = R.choisir_k(t)
    assert 3 not in res["rangs"].index and res["k"] != 3


def test_repli_si_aucun_admissible():
    t = _table(ari_boot_moyen=[0.7, 0.75, 0.75, 0.6], plus_petit_pct=[10, 10, 10, 1])
    res = R.choisir_k(t)
    assert res["k"] == 3 and "règle 5" in res["voie"]  # égalité 3 / 4 : le plus petit


def test_segments_enregistres_coherents():
    import json
    import pytest
    from segmentation import config
    if not config.SEGMENTS.exists():
        pytest.skip("segments non enregistrés")
    s = json.loads(config.SEGMENTS.read_text(encoding="utf-8"))
    assert s["k"] == config.K_RETENU == len(s["segments"])
    assert s["variables"] == config.VARIABLES_PROFIL
    assert all(len(seg["centre"]) == len(config.VARIABLES_PROFIL) for seg in s["segments"])
    assert len({seg["action"] for seg in s["segments"]}) == s["k"]  # une action par segment
    assert s["accord_affectation_apprentissage"] > 0.999
    assert b"\r\n" not in config.SEGMENTS.read_bytes()
