"""Partitions des clients d'apprentissage : K-Means, CAH de Ward, classification mixte, HDBSCAN.

Tous les paramètres viennent de docs/CHOIX.md (fixés avant tout calcul). Ce module ne
charge jamais les avis et n'applique pas la règle de choix de k.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import cophenet, fcluster, linkage
from scipy.spatial.distance import pdist
from sklearn.cluster import HDBSCAN, KMeans
from segmentation.geometrie import affecter  # noqa: F401  (réexporté)
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)


# --- Échantillons -----------------------------------------------------------------------

def ordre_echantillon(identifiants, graine: int) -> list[str]:
    """Ordre aléatoire reproductible des identifiants (triés avant le mélange)."""
    ids = np.array(sorted(set(identifiants)))
    return ids[np.random.default_rng(graine).permutation(len(ids))].tolist()


# --- Outils -------------------------------------------------------------------------------

def renumeroter_par_taille(etiquettes: np.ndarray) -> np.ndarray:
    """Segment 0 = le plus grand, 1 = le suivant… (le bruit, -1, reste -1)."""
    e = np.asarray(etiquettes)
    valides = e[e >= 0]
    tailles = pd.Series(valides).value_counts()
    ordre = sorted(tailles.index, key=lambda s: (-tailles[s], s))
    correspondance = {ancien: nouveau for nouveau, ancien in enumerate(ordre)}
    return np.array([correspondance.get(x, -1) for x in e])


def inertie_r2(x: np.ndarray, etiquettes: np.ndarray) -> float:
    """R² = 1 − inertie intra-classe / inertie totale."""
    totale = ((x - x.mean(axis=0)) ** 2).sum()
    intra = sum(((x[etiquettes == s] - x[etiquettes == s].mean(axis=0)) ** 2).sum()
                for s in np.unique(etiquettes))
    return float(1 - intra / totale)


def indices_internes(x: np.ndarray, etiquettes: np.ndarray, x_sil: np.ndarray,
                     etiquettes_sil: np.ndarray) -> dict:
    """R², Calinski-Harabasz, Davies-Bouldin sur x ; silhouette sur l'échantillon x_sil."""
    return {
        "r2": inertie_r2(x, etiquettes),
        "silhouette": float(silhouette_score(x_sil, etiquettes_sil)),
        "calinski_harabasz": float(calinski_harabasz_score(x, etiquettes)),
        "davies_bouldin": float(davies_bouldin_score(x, etiquettes)),
    }


def jaccard_apparie(reference: np.ndarray, autre: np.ndarray) -> np.ndarray:
    """Pour chaque segment de référence, le plus grand Jaccard avec un segment de `autre`."""
    kr, ka = reference.max() + 1, autre.max() + 1
    commun = np.bincount(reference * ka + autre, minlength=kr * ka).reshape(kr, ka)
    taille_r = commun.sum(axis=1)[:, None]
    taille_a = commun.sum(axis=0)[None, :]
    jaccard = commun / (taille_r + taille_a - commun)
    return jaccard.max(axis=1)


# --- Algorithmes --------------------------------------------------------------------------

def kmeans(x: np.ndarray, k: int, n_init: int, graine: int) -> tuple[np.ndarray, np.ndarray]:
    """K-Means (k-means++) ; renvoie (étiquettes renumérotées par taille, centres dans cet ordre)."""
    m = KMeans(n_clusters=k, init="k-means++", n_init=n_init, max_iter=300,
               random_state=graine).fit(x)
    e = renumeroter_par_taille(m.labels_)
    centres = np.array([x[e == s].mean(axis=0) for s in range(k)])
    return e, centres


def stabilite_bootstrap(x: np.ndarray, references: dict[int, np.ndarray], n_tirages: int,
                        n_init: int, graine: int, garder_partitions: bool = False
                        ) -> dict[int, dict]:
    """Règle de docs/CHOIX.md : un générateur initialisé une fois par la graine ; à chaque
    tirage (avec remise), K-Means refait pour chaque k, puis TOUS les clients sont affectés
    aux centres du tirage ; ARI avec la référence et Jaccard apparié par segment.

    Le générateur ne sert qu'au tirage et à la graine du tirage, jamais dans la boucle sur k :
    refaire le calcul pour un seul k redonne exactement les mêmes tirages et résultats.
    Avec `garder_partitions`, les partitions de chaque tirage sont aussi renvoyées."""
    rng = np.random.default_rng(graine)
    res = {k: {"ari": [], "jaccard": [], "partitions": []} for k in references}
    for _ in range(n_tirages):
        idx = rng.integers(0, len(x), len(x))
        graine_tirage = int(rng.integers(0, 2**31 - 1))
        for k, ref in references.items():
            m = KMeans(n_clusters=k, init="k-means++", n_init=n_init, max_iter=300,
                       random_state=graine_tirage).fit(x[idx])
            e = affecter(x, m.cluster_centers_)
            res[k]["ari"].append(adjusted_rand_score(ref, e))
            res[k]["jaccard"].append(jaccard_apparie(ref, e))
            if garder_partitions:
                res[k]["partitions"].append(e)
    sortie = {}
    for k, v in res.items():
        sortie[k] = {"ari": np.array(v["ari"]), "jaccard": np.vstack(v["jaccard"])}
        if garder_partitions:
            sortie[k]["partitions"] = np.vstack(v["partitions"])
    return sortie


def cah_ward(x: np.ndarray) -> tuple[np.ndarray, float]:
    """CAH de Ward (distance euclidienne) ; renvoie (arbre, corrélation cophénétique)."""
    d = pdist(x)
    arbre = linkage(d, method="ward")
    coph, _ = cophenet(arbre, d)
    return arbre, float(coph)


def couper(arbre: np.ndarray, k: int) -> np.ndarray:
    return renumeroter_par_taille(fcluster(arbre, k, criterion="maxclust") - 1)


def mixte(f_cah: np.ndarray, arbre: np.ndarray, f_tous: np.ndarray, k: int) -> np.ndarray:
    """Coupe de la CAH en k, centres = moyennes, puis K-Means (1 initialisation) sur tous."""
    e = couper(arbre, k)
    centres = np.array([f_cah[e == s].mean(axis=0) for s in range(k)])
    m = KMeans(n_clusters=k, init=centres, n_init=1, max_iter=300).fit(f_tous)
    return renumeroter_par_taille(m.labels_)


def hdbscan(f: np.ndarray, taille_min: int, min_samples: int) -> np.ndarray:
    m = HDBSCAN(min_cluster_size=taille_min, min_samples=min_samples,
                cluster_selection_method="eom").fit(f)
    return renumeroter_par_taille(m.labels_)
