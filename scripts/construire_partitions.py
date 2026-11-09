"""Étape 5 : partitions des 64 805 clients d'apprentissage pour k = 2 à 8, indices, stabilité.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\construire_partitions.py

N'applique PAS la règle de choix de k et ne charge PAS les avis.
Sorties :
    reports/indices_partitions.csv   (versionné : indices et stabilité)
    reports/partitions.md            (versionné : tableau et explications)
    data/processed/partitions.csv    (non versionné : étiquettes)
    captures_brutes/partitions_*.png
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.cluster.hierarchy import dendrogram  # noqa: E402
from sklearn.metrics import adjusted_rand_score  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import acp as A  # noqa: E402
from segmentation import config  # noqa: E402
from segmentation import partitions as P  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402
from segmentation.memoire import exiger_memoire_libre, pic_processus_go  # noqa: E402

BLEU, ORANGE, ENCRE_2, GRILLE, FOND = "#2a78d6", "#eb6834", "#52514e", "#e4e3df", "#fcfcfb"


def fmt(v, d=3):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{v:,.{d}f}".replace(",", " ")


def tableau(entetes, lignes):
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    return "\n".join(out + ["| " + " | ".join(map(str, l)) + " |" for l in lignes])


def chrono(temps: dict, nom: str):
    class _C:
        def __enter__(self):
            self.t = time.perf_counter()

        def __exit__(self, *a):
            temps[nom] = temps.get(nom, 0) + time.perf_counter() - self.t
    return _C()


def main() -> int:
    proteger_sorties()
    temps: dict[str, float] = {}
    libre = exiger_memoire_libre(config.MEMOIRE_MIN_CAH_GO)

    z = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    x = z[config.VARIABLES_PROFIL].to_numpy(dtype=float)
    acp = A.charger(config.ACP)
    f5 = A.projeter(z, acp, config.AXES_MIXTE).to_numpy()
    f4 = A.projeter(z, acp, config.AXES_SENSIBILITE).to_numpy()
    n = len(x)
    position = pd.Series(np.arange(n), index=z.index)

    ordre = P.ordre_echantillon(z.index, config.GRAINE)
    i_commun = position[ordre[:config.N_ECHANTILLON_COMMUN]].to_numpy()
    i_cah = i_commun[:config.N_ECHANTILLON_CAH]
    ks = config.K_VALEURS

    lignes, etiquettes = [], {}

    def ajouter(methode, k, e, x_espace_idx=None, **autres):
        """Indices dans l'espace commun (8 variables préparées)."""
        idx = np.arange(n) if x_espace_idx is None else x_espace_idx
        e_all = np.full(n, -2)
        e_all[idx] = e
        valides = idx[e >= 0]
        sil = np.intersect1d(i_commun, valides)
        ind = P.indices_internes(x[valides], e_all[valides], x[sil], e_all[sil])
        tailles = pd.Series(e_all[valides]).value_counts()
        lignes.append({"methode": methode, "k": k, "clients": len(idx),
                       "segments": int(tailles.size),
                       "plus_petit_pct": 100 * tailles.min() / len(idx),
                       "bruit_pct": 100 * (e < 0).mean(), **ind, **autres})

    # 1. K-Means de référence (8 variables, tous les clients)
    with chrono(temps, "K-Means de référence (20 initialisations, k = 2 à 8)"):
        ref = {k: P.kmeans(x, k, config.N_INIT_REFERENCE, config.GRAINE) for k in ks}
    # 2. Stabilité par bootstrap
    with chrono(temps, "Bootstrap (50 tirages × 7 k × 10 initialisations)"):
        boot = P.stabilite_bootstrap(x, {k: ref[k][0] for k in ks},
                                     config.TIRAGES_BOOTSTRAP_K, config.N_INIT_BOOTSTRAP,
                                     config.GRAINE)
    for k in ks:
        e = ref[k][0]
        etiquettes[f"kmeans_k{k}"] = e
        jac = boot[k]["jaccard"].mean(axis=0)
        ajouter("K-Means (8 variables)", k, e, ari_reference=1.0,
                ari_boot_moyen=float(boot[k]["ari"].mean()),
                ari_boot_min=float(boot[k]["ari"].min()),
                jaccard_min=float(jac.min()),
                jaccard_segments=" ; ".join(f"{j:.2f}" for j in jac))

    # 3. CAH de Ward (8 variables, échantillon de 6 000)
    with chrono(temps, "CAH de Ward, 8 variables (6 000 clients)"):
        arbre8, coph8 = P.cah_ward(x[i_cah])
    for k in ks:
        e = P.couper(arbre8, k)
        ajouter("CAH de Ward (8 variables, 6 000)", k, e, i_cah, cophenetique=coph8,
                ari_reference=adjusted_rand_score(ref[k][0][i_cah], e))

    # 4. Classification mixte (F1–F5) et sensibilité (F1–F4)
    mixtes = {}
    for nom, f, n_axes in (("mixte", f5, config.AXES_MIXTE),
                           ("mixte_sensibilite", f4, config.AXES_SENSIBILITE)):
        with chrono(temps, f"Classification mixte F1–F{n_axes} (CAH 6 000 + consolidation)"):
            arbre, coph = P.cah_ward(f[i_cah])
            mixtes[nom] = {k: P.mixte(f[i_cah], arbre, f, k) for k in ks}
        for k in ks:
            e = mixtes[nom][k]
            etiquettes[f"{nom}_k{k}"] = e
            ajouter(f"Mixte F1–F{n_axes}" + (" (sensibilité)" if n_axes == 4 else ""), k, e,
                    cophenetique=coph, ari_reference=adjusted_rand_score(ref[k][0], e),
                    ari_mixte5_mixte4=(adjusted_rand_score(mixtes["mixte"][k], e)
                                       if nom == "mixte_sensibilite" else None))
        if nom == "mixte":
            arbre5, coph5 = arbre, coph

    # 5. HDBSCAN (F1–F5, tous les clients)
    taille_min = math.ceil(config.PART_MIN_SEGMENT * n)
    with chrono(temps, "HDBSCAN F1–F5 (64 805 clients)"):
        eh = P.hdbscan(f5, taille_min, config.HDBSCAN_MIN_SAMPLES)
    etiquettes["hdbscan"] = eh
    nh = int(eh.max() + 1)
    if nh >= 2:
        ok = eh >= 0
        ari_h = (adjusted_rand_score(ref[nh][0][ok], eh[ok]) if nh in ref else None)
        ajouter("HDBSCAN (F1–F5)", nh, eh, ari_reference=ari_h)
    else:
        lignes.append({"methode": "HDBSCAN (F1–F5)", "k": nh, "clients": n, "segments": nh,
                       "bruit_pct": 100 * (eh < 0).mean()})

    pic = pic_processus_go()
    res = pd.DataFrame(lignes)
    res.to_csv(config.INDICES_PARTITIONS, index=False, encoding="utf-8", lineterminator="\n",
               float_format="%.6g")
    pd.DataFrame(etiquettes, index=z.index).to_csv(config.PARTITIONS, encoding="utf-8",
                                                  lineterminator="\n")

    # --- Rapport ---------------------------------------------------------------------
    km = res[res["methode"] == "K-Means (8 variables)"].set_index("k")
    md = [
        "# Étape 5 : partitions, indices internes et stabilité", "",
        "Rapport généré par `scripts/construire_partitions.py`. Clients d'apprentissage "
        f"({n:,}) seulement ; aucun avis chargé. **La règle de choix de k n'est pas encore "
        "appliquée.** Paramètres fixés avant le calcul (voir `docs/CHOIX.md`).".replace(",", " "),
        "",
        f"Mémoire libre au démarrage : {fmt(libre, 2)} Go (minimum exigé "
        f"{config.MEMOIRE_MIN_CAH_GO:.1f} Go). Pic de mémoire du calcul : {fmt(pic, 2)} Go.", "",
        "## 1. K-Means sur les 8 variables (méthode de référence)", "",
        "Indices internes : R², silhouette (échantillon fixe de 8 000 clients), "
        "Calinski-Harabasz, Davies-Bouldin. Stabilité : 50 tirages bootstrap.", "",
        tableau(["k", "plus petit segment (%)", "R²", "silhouette ↑", "Calinski-Harabasz ↑",
                 "Davies-Bouldin ↓", "ARI bootstrap moyen", "ARI bootstrap min",
                 "Jaccard moyen le plus faible"],
                [[k, fmt(r.plus_petit_pct, 2), fmt(r.r2), fmt(r.silhouette),
                  fmt(r.calinski_harabasz, 0), fmt(r.davies_bouldin), fmt(r.ari_boot_moyen),
                  fmt(r.ari_boot_min), fmt(r.jaccard_min)] for k, r in km.iterrows()]), "",
        "**Jaccard moyen de chaque segment** (segments numérotés du plus grand au plus petit) :",
        "",
        tableau(["k", "Jaccard par segment"],
                [[k, r.jaccard_segments] for k, r in km.iterrows()]), "",
        "**Taille des segments (% des clients)** :", "",
        tableau(["k", "tailles"],
                [[k, " ; ".join(f"{100 * t:.1f}" for t in
                                pd.Series(ref[k][0]).value_counts(normalize=True).sort_index())]
                 for k in ks]), "",
        "## 2. Comparaison des méthodes (indices dans le même espace : les 8 variables "
        "préparées)", "",
        "Silhouette sur l'échantillon commun (8 000), ou sur les 6 000 de la CAH pour la CAH "
        "de Ward. ARI avec K-Means = accord avec la méthode de référence au même k.", "",
        "**Mise en garde** : l'indice de Calinski-Harabasz augmente avec le nombre de clients. "
        "La valeur de la CAH de Ward, calculée sur 6 000 clients, n'est pas comparable aux "
        "valeurs calculées sur les 64 805 clients. Silhouette, Davies-Bouldin et R² restent "
        "comparables entre méthodes.", "",
    ]
    autres = res[res["methode"] != "K-Means (8 variables)"]
    md.append(tableau(
        ["méthode", "k", "clients", "plus petit (%)", "bruit (%)", "R²", "silhouette",
         "Calinski-Harabasz", "Davies-Bouldin", "cophénétique", "ARI avec K-Means"],
        [[r.methode, r.k, fmt(float(r.clients), 0), fmt(r.get("plus_petit_pct"), 2),
          fmt(r.get("bruit_pct"), 1), fmt(r.get("r2")), fmt(r.get("silhouette")),
          fmt(r.get("calinski_harabasz"), 0), fmt(r.get("davies_bouldin")),
          fmt(r.get("cophenetique")), fmt(r.get("ari_reference"))]
         for _, r in autres.iterrows()]))
    sens = res[res["methode"].str.contains("sensibilité")].set_index("k")
    md += ["", "## 3. Contrôle de sensibilité : mixte à 5 axes contre mixte à 4 axes", "",
           "ARI entre les deux partitions (1 = identiques). Description seulement : la décision "
           "de 5 axes ne change pas.", "",
           tableau(["k"] + [str(k) for k in ks],
                   [["ARI mixte 5 / mixte 4"] + [fmt(sens.loc[k, "ari_mixte5_mixte4"]) for k in ks]]),
           "", "## 4. Temps de calcul", "",
           tableau(["étape", "secondes"], [[e, fmt(t, 1)] for e, t in temps.items()]), "",
           "## 5. Ce que ce rapport ne fait pas", "",
           "- Il n'applique pas la règle de choix de k (admissibilité, rangs) : étape suivante.",
           "- Il ne lit pas les avis : les indices externes viennent après le choix de k.", ""]
    (config.DOSSIER_RAPPORTS / "partitions.md").write_text("\n".join(md), encoding="utf-8",
                                                           newline="\n")

    # --- Graphiques ------------------------------------------------------------------
    plt.rcParams.update({"figure.facecolor": FOND, "axes.facecolor": FOND,
                         "savefig.facecolor": FOND, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True, "grid.color": GRILLE,
                         "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
                         "xtick.color": ENCRE_2, "ytick.color": ENCRE_2})
    dossier = config.RACINE / "captures_brutes"
    dossier.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 5, figsize=(17, 3.6))
    for ax, (col, titre) in zip(axes, [("r2", "R²"), ("silhouette", "Silhouette ↑"),
                                       ("calinski_harabasz", "Calinski-Harabasz ↑"),
                                       ("davies_bouldin", "Davies-Bouldin ↓"),
                                       ("ari_boot_moyen", "ARI bootstrap moyen")]):
        ax.plot(km.index, km[col], color=BLEU, marker="o", linewidth=2, markersize=6)
        if col == "ari_boot_moyen":
            ax.fill_between(km.index, km["ari_boot_min"], km[col], color=BLEU, alpha=0.15,
                            linewidth=0, label="du minimum à la moyenne")
            ax.legend(frameon=False, fontsize=8, loc="lower left")
        ax.set_title(titre)
        ax.set_xlabel("k")
        ax.set_xticks(ks)
    fig.suptitle("K-Means sur les 8 variables : indices internes et stabilité selon k",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(dossier / "partitions_indices_k.png", dpi=120)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
    for ax, arbre, titre in ((axes[0], arbre8, f"CAH de Ward, 8 variables (cophénétique "
                                                f"{coph8:.3f})"),
                             (axes[1], arbre5, f"Classification mixte : CAH de Ward sur F1–F5 (cophénétique "
                                         f"{coph5:.3f})")):
        dendrogram(arbre, truncate_mode="lastp", p=30, ax=ax, no_labels=True,
                   color_threshold=0, above_threshold_color=BLEU)
        ax.set_title(titre)
        ax.set_ylabel("Hauteur de fusion (Ward)")
        ax.grid(False)
    fig.suptitle("Dendrogrammes (30 dernières fusions, 6 000 clients)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(dossier / "partitions_dendrogrammes.png", dpi=120)
    plt.close(fig)

    print(f"Terminé. Pic mémoire {fmt(pic, 2)} Go ; temps total {fmt(sum(temps.values()), 0)} s")
    print("Rapport : reports/partitions.md ; indices : reports/indices_partitions.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
