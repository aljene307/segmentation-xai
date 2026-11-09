"""Tests des outils de partition sur de petites données construites à la main."""

import numpy as np
import pytest
from sklearn.metrics import adjusted_rand_score

from segmentation import partitions as P


def _trois_groupes(n=300, graine=0):
    rng = np.random.default_rng(graine)
    centres = np.array([[0, 0], [8, 0], [0, 8]])
    x = np.vstack([c + rng.normal(size=(n, 2)) for c in centres])
    vrai = np.repeat([0, 1, 2], n)
    return x, vrai


def test_ordre_echantillon_reproductible_et_independant_de_l_ordre():
    ids = [f"c{i:03d}" for i in range(100)]
    a = P.ordre_echantillon(ids, 42)
    assert a == P.ordre_echantillon(list(reversed(ids)), 42)
    assert sorted(a) == sorted(ids) and a != sorted(ids)
    # échantillons emboîtés : les 60 premiers sont inclus dans les 80 premiers
    assert set(a[:60]) <= set(a[:80])


def test_renumeroter_par_taille_garde_le_bruit():
    e = P.renumeroter_par_taille(np.array([5, 5, 2, 2, 2, -1, 7]))
    assert e.tolist() == [1, 1, 0, 0, 0, -1, 2]


def test_affecter_au_centre_le_plus_proche():
    centres = np.array([[0.0, 0.0], [10.0, 0.0]])
    assert P.affecter(np.array([[1.0, 0.0], [9.0, 1.0]]), centres).tolist() == [0, 1]


def test_r2_cas_limites():
    x = np.array([[0.0], [0.0], [10.0], [10.0]])
    assert P.inertie_r2(x, np.array([0, 0, 1, 1])) == pytest.approx(1.0)
    assert P.inertie_r2(x, np.array([0, 0, 0, 0])) == pytest.approx(0.0)


def test_jaccard_apparie_a_la_main():
    ref = np.array([0, 0, 0, 0, 1, 1])
    autre = np.array([0, 0, 0, 1, 1, 1])
    # segment 0 : avec 0 -> 3/4 ; segment 1 : avec 1 -> 2/3
    assert P.jaccard_apparie(ref, autre) == pytest.approx([3 / 4, 2 / 3])
    # renuméroter l'autre partition ne change rien
    assert P.jaccard_apparie(ref, 1 - autre) == pytest.approx([3 / 4, 2 / 3])


def test_kmeans_retrouve_des_groupes_nets_et_est_reproductible():
    x, vrai = _trois_groupes()
    e1, c1 = P.kmeans(x, 3, 5, 42)
    e2, c2 = P.kmeans(x, 3, 5, 42)
    assert adjusted_rand_score(vrai, e1) > 0.99
    assert np.array_equal(e1, e2) and np.allclose(c1, c2)
    assert np.bincount(e1).tolist() == sorted(np.bincount(e1).tolist(), reverse=True)


def test_bootstrap_stable_sur_groupes_nets():
    x, _ = _trois_groupes(n=150)
    ref = {3: P.kmeans(x, 3, 5, 42)[0]}
    b = P.stabilite_bootstrap(x, ref, 5, 3, 42)
    assert b[3]["ari"].shape == (5,) and b[3]["jaccard"].shape == (5, 3)
    assert b[3]["ari"].min() > 0.98 and b[3]["jaccard"].min() > 0.98
    b2 = P.stabilite_bootstrap(x, ref, 5, 3, 42)
    assert np.array_equal(b[3]["ari"], b2[3]["ari"])  # reproductible


def test_bootstrap_instable_si_k_trop_grand_sur_un_seul_nuage():
    rng = np.random.default_rng(3)
    x = rng.normal(size=(600, 2))
    ref = {6: P.kmeans(x, 6, 5, 42)[0]}
    b = P.stabilite_bootstrap(x, ref, 5, 3, 42)
    assert b[6]["ari"].mean() < 0.95  # un nuage continu découpé en 6 bouge d'un tirage à l'autre


def test_cah_ward_et_mixte():
    x, vrai = _trois_groupes(n=100)
    arbre, coph = P.cah_ward(x)
    assert coph > 0.8
    assert adjusted_rand_score(vrai, P.couper(arbre, 3)) > 0.99
    e = P.mixte(x[::2], P.cah_ward(x[::2])[0], x, 3)
    assert adjusted_rand_score(vrai, e) > 0.99


def test_hdbscan_marque_le_bruit():
    x, _ = _trois_groupes(n=200)
    x = np.vstack([x, [[50, 50], [-40, 30]]])
    e = P.hdbscan(x, 50, 10)
    assert e.max() + 1 == 3 and (e[-2:] == -1).all()
