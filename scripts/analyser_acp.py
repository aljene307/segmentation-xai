"""ACP normée : apprise sur les 80 % préparés, enregistrée, projetée sur les 20 %.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\analyser_acp.py

Sorties :
    models/acp.json                    (versionné)
    reports/acp.md                     (versionné)
    captures_brutes/acp_*.png          (à relire)

Si models/acp.json existe déjà, l'ACP est recalculée et comparée : le script
s'arrête en cas de différence.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import acp as A  # noqa: E402
from segmentation import config  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402

COURTS = {
    "recence_j": "Récence",
    "frequence": "Fréquence",
    "montant_rs": "Montant",
    "part_frais_port": "Part frais port",
    "mensualites_moy": "Mensualités",
    "articles_par_commande": "Articles/commande",
    "delai_livraison_moy_j": "Délai livraison",
    "ecart_prevision_moy_j": "Écart date promise",
}
BLEU, ORANGE, ENCRE, ENCRE_2, GRILLE, FOND = (
    "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb")


def fmt(v, d=2):
    return f"{v:,.{d}f}".replace(",", " ")


def tableau(entetes, lignes):
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    return "\n".join(out + ["| " + " | ".join(map(str, l)) + " |" for l in lignes])


def style():
    plt.rcParams.update({
        "figure.facecolor": FOND, "axes.facecolor": FOND, "savefig.facecolor": FOND,
        "axes.edgecolor": ENCRE_2, "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": ENCRE_2, "ytick.color": ENCRE_2, "font.size": 9,
        "axes.titlesize": 10, "axes.titleweight": "bold", "axes.grid": True,
        "grid.color": GRILLE, "grid.linewidth": 0.6})


def figure_valeurs_propres(acp, chemin):
    vp = np.asarray(acp["valeurs_propres"])
    k = acp["decision"]["retenus"]
    x = np.arange(1, len(vp) + 1)
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4))
    a.bar(x, vp, color=[BLEU if i <= k else "#b9b8b2" for i in x])
    a.plot(x, vp, color=ENCRE_2, linewidth=1, marker="o", markersize=4)
    a.axhline(1, color=ORANGE, linewidth=1.5, linestyle="--")
    a.text(len(vp) + 0.4, 1.02, "Kaiser = 1", color=ENCRE_2, ha="right", va="bottom")
    a.set_xticks(x, [f"F{i}" for i in x])
    a.set_ylabel("Valeur propre")
    a.set_title(f"Valeurs propres (bleu : {k} axes retenus)")
    cum = 100 * np.cumsum(vp) / vp.sum()
    b.plot(x, cum, color=BLEU, linewidth=2, marker="o", markersize=5)
    b.axhline(100 * acp["part_minimale"], color=ORANGE, linewidth=1.5, linestyle="--")
    b.text(1, 100 * acp["part_minimale"] + 1, f"{100 * acp['part_minimale']:.0f} %",
           color=ENCRE_2, va="bottom")
    for xi, c in zip(x, cum):
        b.annotate(f"{c:.0f} %", (xi, c), xytext=(0, 6), textcoords="offset points",
                   ha="center", fontsize=8, color=ENCRE_2)
    b.set_xticks(x, [f"F{i}" for i in x])
    b.set_ylim(0, 105)
    b.set_ylabel("Part cumulée de l'information (%)")
    b.set_title("Part cumulée")
    fig.tight_layout()
    fig.savefig(chemin, dpi=130)
    plt.close(fig)


def figure_cercles(corr, acp, k, chemin):
    paires = list(itertools.combinations(range(k), 2))
    n = len(paires)
    colonnes = min(3, n)
    lignes = int(np.ceil(n / colonnes))
    fig, axes = plt.subplots(lignes, colonnes, figsize=(5 * colonnes, 5 * lignes), squeeze=False)
    vp = np.asarray(acp["valeurs_propres"])
    part = 100 * vp / vp.sum()
    t = np.linspace(0, 2 * np.pi, 300)
    for ax, (i, j) in zip(axes.flat, paires):
        ax.plot(np.cos(t), np.sin(t), color=ENCRE_2, linewidth=0.8)
        ax.axhline(0, color=GRILLE, linewidth=0.8)
        ax.axvline(0, color=GRILLE, linewidth=0.8)
        for v in corr.index:
            x, y = corr.iloc[corr.index.get_loc(v), i], corr.iloc[corr.index.get_loc(v), j]
            qualite = x ** 2 + y ** 2
            couleur = BLEU if qualite >= 0.25 else "#9a9992"
            ax.annotate("", xy=(x, y), xytext=(0, 0),
                        arrowprops={"arrowstyle": "->", "color": couleur, "linewidth": 1.5})
            ax.text(x * 1.08, y * 1.08, COURTS[v], fontsize=8, color=ENCRE,
                    ha="left" if x >= 0 else "right", va="bottom" if y >= 0 else "top")
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        ax.set_aspect("equal")
        ax.grid(False)
        ax.set_xlabel(f"F{i + 1} ({part[i]:.1f} %)")
        ax.set_ylabel(f"F{j + 1} ({part[j]:.1f} %)")
        ax.set_title(f"Cercle des corrélations F{i + 1} – F{j + 1}")
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    fig.text(0.5, 0.005, "Bleu : variable bien représentée sur ce plan (cos² cumulé ≥ 0,25) ; "
             "gris : mal représentée.", ha="center", color=ENCRE_2, fontsize=8)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(chemin, dpi=110)
    plt.close(fig)


def figure_carte(scores, chemin):
    fig, ax = plt.subplots(figsize=(7, 6))
    hb = ax.hexbin(scores["F1"], scores["F2"], gridsize=70, bins="log", cmap="Blues", mincnt=1)
    fig.colorbar(hb, ax=ax, label="Clients par case (échelle log)")
    ax.set_xlabel("F1")
    ax.set_ylabel("F2")
    ax.set_title("Clients d'apprentissage sur le plan F1 – F2 (densité)")
    ax.grid(False)
    fig.tight_layout()
    fig.savefig(chemin, dpi=120)
    plt.close(fig)


def main() -> int:
    proteger_sorties()
    style()
    variables = config.VARIABLES_PROFIL
    z_app = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    z_cote = pd.read_csv(config.PREPARES_MISE_DE_COTE, index_col="customer_unique_id")
    profils = pd.read_csv(config.PROFILS_APPRENTISSAGE, index_col="customer_unique_id",
                          usecols=["customer_unique_id", "premier_achat"])

    acp = A.apprendre(z_app, variables, config.PART_CUMULEE_MINIMALE)
    if config.ACP.exists():
        if A.charger(config.ACP) != acp:
            raise SystemExit("ÉCART : l'ACP recalculée diffère de models/acp.json")
        etat = "ACP recalculée identique au fichier enregistré"
    else:
        A.sauver(acp, config.ACP)
        etat = "ACP enregistrée (premier apprentissage)"
    acp = A.charger(config.ACP)

    vp = np.asarray(acp["valeurs_propres"])
    d = acp["decision"]
    k = d["retenus"]
    axes = A.noms_axes(acp)
    corr = A.correlations(acp)
    c2 = A.cos2(acp)
    contrib = A.contributions(acp)
    s_app = A.projeter(z_app, acp)
    s_cote = A.projeter(z_cote, acp)

    date = pd.to_datetime(profils.loc[s_app.index, "premier_achat"])
    jours = (date - pd.Timestamp("1970-01-01")).dt.days.astype(float)
    corr_date = {a: float(np.corrcoef(s_app[a], jours)[0, 1]) for a in axes[:k]}

    md = ["# ACP normée", "",
          "Rapport généré par `scripts/analyser_acp.py`. ACP apprise sur les "
          f"{fmt(len(z_app), 0)} clients d'apprentissage préparés (80 %), enregistrée dans "
          f"`models/acp.json`, puis appliquée telle quelle aux {fmt(len(z_cote), 0)} clients "
          "mis de côté. Règles fixées et poussées avant le calcul (voir `docs/CHOIX.md`).", "",
          f"État : {etat}.", "",
          "## 1. Valeurs propres", "",
          tableau(["axe", "valeur propre", "% de l'information", "% cumulé", "> 1 (Kaiser)"],
                  [[a, fmt(vp[i], 3), fmt(100 * vp[i] / vp.sum()),
                    fmt(100 * vp[:i + 1].sum() / vp.sum()), "oui" if vp[i] > 1 else "non"]
                   for i, a in enumerate(axes)]), "",
          "## 2. Nombre d'axes retenus", "",
          tableau(["règle", "nombre d'axes", "rôle"], [
              ["Kaiser (valeur propre > 1)", d["kaiser"], "décide (avec la part cumulée)"],
              [f"part cumulée ≥ {100 * acp['part_minimale']:.0f} %", d["part_cumulee"],
               "décide (avec Kaiser)"],
              ["coude (plus forte chute après l'axe)", d["coude_indicatif"],
               "indicatif seulement"],
              ["**décision : max(Kaiser, part cumulée)**", f"**{k}**", ""],
          ]), "",
          f"Les {k} axes retenus portent {fmt(100 * vp[:k].sum() / vp.sum())} % de "
          "l'information.", "",
          "## 3. Corrélations variables–axes", "",
          "Corrélation entre chaque variable préparée et chaque axe. En gras : axes retenus.", "",
          tableau(["variable"] + [f"**{a}**" if i < k else a for i, a in enumerate(axes)],
                  [[COURTS[v]] + [fmt(x) for x in corr.loc[v]] for v in variables]), "",
          "## 4. cos² des variables sur les axes retenus", "",
          "cos² = corrélation au carré : part de la variable expliquée par l'axe. La somme sur "
          "les axes retenus mesure la qualité de représentation de la variable.", "",
          tableau(["variable"] + axes[:k] + ["somme (qualité)"],
                  [[COURTS[v]] + [fmt(x) for x in c2.loc[v, axes[:k]]]
                   + [fmt(c2.loc[v, axes[:k]].sum())] for v in variables]), "",
          "## 5. Contributions des variables aux axes retenus (%)", "",
          tableau(["variable"] + axes[:k],
                  [[COURTS[v]] + [fmt(x, 1) for x in contrib.loc[v, axes[:k]]]
                   for v in variables]), "",
          "## 6. Description des axes retenus (base de leur nom)", "",
          f"Variables retenues pour nommer un axe : |corrélation| ≥ {config.SEUIL_NOM_AXE:g}, "
          "sinon les 2 plus fortes.", ""]
    for a in axes[:k]:
        desc = A.description_axe(corr[a], config.SEUIL_NOM_AXE)
        md += [f"**{a}** ({fmt(100 * vp[axes.index(a)] / vp.sum())} %) — {desc['regle']} : "
               + ", ".join(f"{COURTS[v]} ({fmt(c)})" for v, c in desc["variables"].items()),
               "",
               "- côté + : " + ", ".join(p.replace(v, COURTS[v]) for v, p in
                                         zip(desc["variables"], desc["pole_plus"])),
               "- côté − : " + ", ".join(p.replace(v, COURTS[v]) for v, p in
                                         zip(desc["variables"], desc["pole_moins"])), ""]

    lignes_temps = []
    for a in axes[:k]:
        cr = float(corr.loc["recence_j", a])
        autres = corr[a].drop("recence_j")
        autres = autres[autres.abs() >= 0.3]
        lignes_temps.append([a, fmt(cr), fmt(corr_date[a]),
                             "**oui**" if A.axe_du_temps(cr, corr_date[a], config.SEUIL_AXE_TEMPS)
                             else "non",
                             ", ".join(f"{COURTS[v]} ({fmt(c)})" for v, c in autres.items())
                             or "—"])
    md += ["## 7. Vérification de l'axe du temps", "",
           f"Axe du temps si |corr(Récence, axe)| ≥ {config.SEUIL_AXE_TEMPS:g} ET "
           f"|corr(coordonnées, date du premier achat)| ≥ {config.SEUIL_AXE_TEMPS:g}. "
           "Les autres variables qui pèsent (|corr| ≥ 0,3) sont décrites, sans être une condition.",
           "",
           tableau(["axe", "corr. Récence", "corr. date d'achat", "axe du temps",
                    "autres variables (|corr| ≥ 0,3)"], lignes_temps), "",
           "## 8. Projection des 20 % mis de côté", "",
           "Variance des coordonnées : sur les 80 %, elle vaut la valeur propre (par "
           "construction) ; sur les 20 %, des valeurs proches montrent que les axes se "
           "transposent à des clients jamais vus.", "",
           tableau(["axe", "valeur propre", "variance 80 %", "variance 20 %", "moyenne 20 %"],
                   [[a, fmt(vp[i], 3), fmt(s_app[a].var(ddof=0), 3),
                     fmt(s_cote[a].var(ddof=0), 3), fmt(s_cote[a].mean(), 3)]
                    for i, a in enumerate(axes[:k])]), ""]
    # 9. Stabilité par bootstrap (description seulement).
    blocs = {"F1_F2": [0, 1], "F3_F5": [2, 3, 4], f"F1_F{k}": list(range(k))}
    boot = A.stabilite_bootstrap(z_app, acp, config.TIRAGES_BOOTSTRAP_ACP, config.GRAINE, blocs)

    def q(col, p):
        return boot[col].quantile(p)

    md += ["## 9. Noms des axes retenus", "",
           tableau(["axe", "nom", "% de l'information"],
                   [[a, config.NOMS_AXES[a], fmt(100 * vp[i] / vp.sum())]
                    for i, a in enumerate(axes[:k])]), "",
           "## 10. Stabilité des axes par bootstrap (description)", "",
           f"{config.TIRAGES_BOOTSTRAP_ACP} tirages avec remise des {fmt(len(z_app), 0)} clients "
           f"d'apprentissage (graine {config.GRAINE}) ; l'ACP est refaite sur chaque tirage. "
           "|cos| = 1 : axe identique ; un |cos| bas avec un « meilleur |cos| » haut signifie que "
           "l'axe existe toujours mais a changé de rang.", "",
           tableau(["axe", "|cos| médian (même rang)", "|cos| 5e centile", "|cos| minimum",
                    "meilleur |cos| médian", "meilleur |cos| 5e centile",
                    "valeur propre : médiane [5e – 95e centile]"],
                   [[a, fmt(q(f"cos_{a}", .5), 3), fmt(q(f"cos_{a}", .05), 3),
                     fmt(boot[f"cos_{a}"].min(), 3), fmt(q(f"meilleur_{a}", .5), 3),
                     fmt(q(f"meilleur_{a}", .05), 3),
                     f"{fmt(q(f'vp_{a}', .5), 3)} [{fmt(q(f'vp_{a}', .05), 3)} – "
                     f"{fmt(q(f'vp_{a}', .95), 3)}]"] for a in axes[:k + 1]]), "",
           "**Sous-espaces** : plus petit cosinus principal entre le sous-espace d'origine et "
           "celui du tirage (1 = même sous-espace, même si les axes y ont tourné).", "",
           tableau(["sous-espace", "médiane", "5e centile", "minimum"],
                   [[n.replace("_", " – "), fmt(q(f"bloc_{n}", .5), 4),
                     fmt(q(f"bloc_{n}", .05), 4), fmt(boot[f"bloc_{n}"].min(), 4)]
                    for n in blocs]), "",
           "**Nombre d'axes que donnerait la règle sur chaque tirage** : "
           + ", ".join(f"{int(n)} axes : {int(c)} tirages"
                       for n, c in boot["retenus"].value_counts().sort_index().items())
           + ". (Description : la décision reste celle calculée sur les 80 %.)", ""]
    (config.DOSSIER_RAPPORTS / "acp.md").write_text("\n".join(md), encoding="utf-8",
                                                    newline="\n")

    dossier = config.RACINE / "captures_brutes"
    dossier.mkdir(exist_ok=True)
    figure_valeurs_propres(acp, dossier / "acp_valeurs_propres.png")
    figure_cercles(corr, acp, k, dossier / "acp_cercles.png")
    figure_carte(s_app, dossier / "acp_carte_F1_F2.png")
    print(f"ACP : {etat} ; {k} axes retenus")
    print("Rapport : reports/acp.md ; graphiques : captures_brutes/acp_*.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
