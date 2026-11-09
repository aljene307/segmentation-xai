"""Exploration des données brutes : graphiques dans captures_brutes/, chiffres dans reports/.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\exploration.py

Les graphiques vont dans captures_brutes/ (ignoré par Git) tant qu'ils ne sont pas relus.
Aucune colonne d'avis n'est chargée. Montants en R$.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation import exploration as ex  # noqa: E402
from segmentation.donnees import charger_tables  # noqa: E402

SORTIE = config.RACINE / "captures_brutes"
BLEU, ORANGE, GRIS_NEUTRE = "#2a78d6", "#eb6834", "#f0efec"
ENCRE, ENCRE_2, FOND = "#0b0b0b", "#52514e", "#fcfcfb"

VARIABLES = {
    "montant_articles": "Montant des articles (R$)",
    "frais_port": "Frais de port (R$)",
    "nb_articles": "Nombre d'articles",
    "nb_vendeurs": "Nombre de vendeurs",
    "mensualites": "Nombre de mensualités",
    "delai_livraison_j": "Délai de livraison (jours)",
    "ecart_prevision_j": "Écart à la date promise (jours, > 0 = retard)",
}

plt.rcParams.update({
    "figure.facecolor": FOND, "axes.facecolor": FOND, "savefig.facecolor": FOND,
    "axes.edgecolor": ENCRE_2, "axes.labelcolor": ENCRE, "text.color": ENCRE,
    "xtick.color": ENCRE_2, "ytick.color": ENCRE_2, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": "#e4e3df",
    "grid.linewidth": 0.6, "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
})


def fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def figure_mois(par_mois, chemin):
    fig, ax = plt.subplots(figsize=(11, 4))
    x = np.arange(len(par_mois))
    ax.bar(x - 0.2, par_mois["toutes"], 0.4, color=BLEU, label="Toutes les commandes")
    ax.bar(x + 0.2, par_mois["livrees"], 0.4, color=ORANGE, label="Commandes livrées")
    ax.set_xticks(x, [str(p) for p in par_mois.index], rotation=90)
    ax.set_ylabel("Commandes")
    ax.set_title("Commandes par mois d'achat")
    ax.legend(frameon=False, loc="upper left")
    for i, (_, r) in enumerate(par_mois.iterrows()):
        if r["toutes"] < 500:
            ax.annotate(fmt(r["toutes"]), (i - 0.2, r["toutes"]), ha="center",
                        va="bottom", fontsize=7, color=ENCRE_2, xytext=(0, 2),
                        textcoords="offset points")
    fig.tight_layout()
    fig.savefig(chemin, dpi=130)
    plt.close(fig)


def figure_distributions(t, chemin):
    noms = list(VARIABLES)
    fig, axes = plt.subplots(len(noms), 2, figsize=(10, 2.2 * len(noms)))
    for ligne, c in zip(axes, noms):
        x = t[c].dropna()
        ligne[0].hist(x, bins=60, color=BLEU)
        ligne[0].set_title(f"{VARIABLES[c]} — brut")
        if (x >= 0).all():
            ligne[1].hist(np.log1p(x), bins=60, color=BLEU)
            ligne[1].set_title("après log(1 + x)")
        else:
            ligne[1].hist(x.clip(*x.quantile([0.01, 0.99])), bins=60, color=BLEU)
            ligne[1].set_title("zoom 1er–99e centile (valeurs négatives : pas de log)")
    fig.tight_layout()
    fig.savefig(chemin, dpi=110)
    plt.close(fig)


def figure_boites(t, chemin):
    noms = list(VARIABLES)
    fig, axes = plt.subplots(1, len(noms), figsize=(14, 4))
    for ax, c in zip(axes, noms):
        ax.boxplot(t[c].dropna(), widths=0.5, flierprops={"markersize": 2, "alpha": 0.3,
                   "markeredgecolor": BLEU}, medianprops={"color": ORANGE},
                   boxprops={"color": ENCRE_2}, whiskerprops={"color": ENCRE_2},
                   capprops={"color": ENCRE_2})
        ax.set_title(VARIABLES[c], fontsize=8, wrap=True)
        ax.set_xticks([])
    fig.suptitle("Valeurs extrêmes (boîtes à moustaches, règle 1,5 × écart interquartile)")
    fig.tight_layout()
    fig.savefig(chemin, dpi=120)
    plt.close(fig)


def figure_correlations(corr, chemin):
    cmap = LinearSegmentedColormap.from_list("div", [ORANGE, GRIS_NEUTRE, BLEU])
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.imshow(corr, cmap=cmap, vmin=-1, vmax=1)
    etiquettes = [VARIABLES[c].split(" (")[0] for c in corr.columns]
    ax.set_xticks(range(len(corr)), etiquettes, rotation=45, ha="right")
    ax.set_yticks(range(len(corr)), etiquettes)
    ax.grid(False)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iat[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.8, label="Corrélation de Spearman")
    ax.set_title("Corrélations entre variables (par commande livrée)")
    fig.tight_layout()
    fig.savefig(chemin, dpi=130)
    plt.close(fig)


def figure_etats(etats, delais, chemin):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 6))
    y = np.arange(len(etats))[::-1]
    a1.barh(y, etats["pct"], color=BLEU)
    a1.set_yticks(y, etats.index)
    a1.set_xlabel("% des clients")
    a1.set_title("Clients par État")
    for yi, v in zip(y, etats["pct"]):
        if v >= 2:
            a1.text(v, yi, f" {v:.1f} %", va="center", fontsize=7, color=ENCRE_2)
    d = delais.reindex(etats.index)
    a2.barh(y, d, color=BLEU)
    a2.set_yticks(y, etats.index)
    a2.set_xlabel("Délai de livraison médian (jours)")
    a2.set_title("Délai médian par État (même ordre)")
    fig.tight_layout()
    fig.savefig(chemin, dpi=120)
    plt.close(fig)


def tableau(entetes, lignes):
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    return "\n".join(out + ["| " + " | ".join(map(str, l)) + " |" for l in lignes])


def main() -> int:
    SORTIE.mkdir(exist_ok=True)
    tables = charger_tables(sauf=("geolocalisation",))

    perte = ex.clients_sans_commande_livree(tables["clients"], tables["commandes"])
    par_mois = ex.commandes_par_mois(tables["commandes"])
    t = ex.table_commandes(tables)
    extremes = ex.valeurs_extremes(t, list(VARIABLES))
    corr = ex.correlations(t, list(VARIABLES))
    etats = ex.repartition_etats(t)
    delais = t.groupby("customer_state")["delai_livraison_j"].median()
    coupure = ex.effet_coupure(tables["commandes"], t).loc["2017-01":]
    semaines = ex.livraisons_par_semaine(tables["commandes"], "2018-07-01")

    figure_mois(par_mois, SORTIE / "commandes_par_mois.png")
    figure_distributions(t, SORTIE / "distributions.png")
    figure_boites(t, SORTIE / "valeurs_extremes.png")
    figure_correlations(corr, SORTIE / "correlations.png")
    figure_etats(etats, delais, SORTIE / "etats.png")

    md = ["# Exploration des données brutes Olist", "",
          "Rapport généré par `scripts/exploration.py`. Variables calculées par commande "
          "livrée (statut `delivered` avec date de livraison). Montants en R$. "
          "Aucune colonne d'avis utilisée.", "",
          "## Clients perdus en ne gardant que les commandes livrées", "",
          tableau(["mesure", "valeur"], [["vrais clients (toutes commandes)", fmt(perte["clients"])],
                                          ["clients avec au moins une commande livrée", fmt(perte["gardes"])],
                                          ["clients perdus", fmt(perte["perdus"])],
                                          ["part perdue (%)", f"{100 * perte['perdus'] / perte['clients']:.2f}"]]),
          "", "## Commandes par mois d'achat", "",
          tableau(["mois", "toutes", "livrées"],
                  [[str(m), fmt(r["toutes"]), fmt(r["livrees"])] for m, r in par_mois.iterrows()]),
          "", "## Effet de coupure en fin de période", "",
          "Par mois d'achat. Délais en jours ; délai promis = date estimée moins date d'achat.", "",
          tableau(["mois", "commandes", "% livrées", "délai médian", "délai 90e centile",
                   "délai promis médian", "% SP"],
                  [[str(m), fmt(r["commandes"]), r["pct_livrees"], r["delai_median"],
                    r["delai_p90"], r["delai_promis_median"], r["pct_sp"]]
                   for m, r in coupure.iterrows()]),
          "", "Livraisons par semaine de livraison, depuis juillet 2018 :", "",
          tableau(["semaine", "livraisons"], [[str(w), fmt(n)] for w, n in semaines.items()]),
          "", "## Distributions et valeurs extrêmes (par commande livrée)", "",
          tableau(["variable", "min", "médiane", "moyenne", "max", "asymétrie",
                   "% hors moustaches", "toujours ≥ 0"],
                  [[VARIABLES[c], f"{r['min']:.2f}", f"{r['mediane']:.2f}", f"{r['moyenne']:.2f}",
                    f"{r['max']:.2f}", f"{r['asymetrie']:.2f}", f"{r['pct_hors_moustaches']:.1f}",
                    "oui" if r["positive_ou_nulle"] else "non"] for c, r in extremes.iterrows()]),
          "", "## Corrélations de Spearman", "",
          tableau([""] + [c for c in corr.columns],
                  [[i] + [f"{v:.2f}" for v in r] for i, r in corr.iterrows()]),
          "", "## Clients par État (État de la dernière commande livrée)", "",
          tableau(["État", "clients", "%", "% cumulé", "délai médian (j)"],
                  [[s, fmt(r["clients"]), r["pct"], r["pct_cumule"], f"{delais[s]:.1f}"]
                   for s, r in etats.iterrows()]), ""]
    sortie = config.DOSSIER_RAPPORTS / "exploration.md"
    sortie.write_text("\n".join(md), encoding="utf-8", newline="\n")
    print("Graphiques : captures_brutes/ ; rapport : reports/exploration.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
