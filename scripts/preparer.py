"""Apprend la préparation sur les 80 %, l'enregistre, l'applique aux 80 % et aux 20 %.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\preparer.py

Sorties :
    models/preparation.json                    (versionné : paramètres appris)
    data/processed/prepares_apprentissage.csv  (non versionné)
    data/processed/prepares_mise_de_cote.csv   (non versionné)
    reports/preparation.md                     (versionné : avant/après)
    captures_brutes/preparation_avant_apres.png

Si models/preparation.json existe déjà, les paramètres sont recalculés et comparés :
le script s'arrête en cas de différence (rien ne change en silence).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation import preparation as prepa  # noqa: E402
from segmentation.comparaison import presque_egaux  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402

NOMS = {
    "recence_j": "Récence (jours)",
    "frequence": "Fréquence (commandes)",
    "montant_rs": "Montant (R$)",
    "part_frais_port": "Part des frais de port",
    "mensualites_moy": "Mensualités moyennes",
    "articles_par_commande": "Articles par commande",
    "delai_livraison_moy_j": "Délai de livraison moyen (jours)",
    "ecart_prevision_moy_j": "Écart à la date promise (jours)",
}
BLEU, ENCRE_2, FOND = "#2a78d6", "#52514e", "#fcfcfb"


def fmt(v, d=2):
    return f"{v:,.{d}f}".replace(",", " ")


def tableau(entetes, lignes):
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    return "\n".join(out + ["| " + " | ".join(map(str, l)) + " |" for l in lignes])


def lire(chemin: Path) -> pd.DataFrame:
    return pd.read_csv(chemin, index_col="customer_unique_id")


def figure(brut: pd.DataFrame, prepare: pd.DataFrame, prep: dict, chemin: Path) -> None:
    plt.rcParams.update({"figure.facecolor": FOND, "axes.facecolor": FOND,
                         "savefig.facecolor": FOND, "axes.spines.top": False,
                         "axes.spines.right": False, "font.size": 8,
                         "axes.titlesize": 9, "axes.titleweight": "bold",
                         "xtick.color": ENCRE_2, "ytick.color": ENCRE_2})
    variables = prep["variables"]
    fig, axes = plt.subplots(len(variables), 2, figsize=(10, 2.0 * len(variables)))
    for (a, b), v in zip(axes, variables):
        a.hist(brut[v], bins=60, color=BLEU)
        a.set_title(f"{NOMS[v]} — brut")
        b.hist(prepare[v], bins=60, color=BLEU)
        etapes = ("log → " if prep["parametres"][v]["log"] else "") + "écrêtage → standardisation"
        b.set_title(f"après {etapes}")
    fig.tight_layout()
    fig.savefig(chemin, dpi=105)
    plt.close(fig)


def main() -> int:
    proteger_sorties()
    app = lire(config.PROFILS_APPRENTISSAGE)
    cote = lire(config.PROFILS_MISE_DE_COTE)
    variables = config.VARIABLES_PROFIL

    prep = prepa.apprendre(app, variables, config.VARIABLES_BORNEES,
                           config.SEUIL_ASYMETRIE_LOG, config.CENTILES_ECRETAGE)
    if config.PREPARATION.exists():
        if not presque_egaux(prepa.charger(config.PREPARATION), prep):
            raise SystemExit("ÉCART : les paramètres recalculés diffèrent de models/preparation.json")
        etat = "paramètres recalculés identiques au fichier enregistré"
    else:
        prepa.sauver(prep, config.PREPARATION)
        etat = "paramètres enregistrés (premier apprentissage)"
    prep = prepa.charger(config.PREPARATION)  # on applique ce qui est relu du fichier

    sorties = {}
    for nom, df, chemin in (("80 %", app, config.PREPARES_APPRENTISSAGE),
                            ("20 %", cote, config.PREPARES_MISE_DE_COTE)):
        z = prepa.appliquer(df, prep)
        ind = prepa.indicateur_ecretage(df, prep)
        z.join(ind).to_csv(chemin, encoding="utf-8", lineterminator="\n")
        sorties[nom] = (z, ind, prepa.ecretages(df, prep))

    z_app, ind_app, ec_app = sorties["80 %"]
    z_cote, ind_cote, ec_cote = sorties["20 %"]
    unites = prepa.seuils_en_unites(prep)
    p = prep["parametres"]

    # Alternative écartée 1 / 99, à titre de comparaison seulement (non utilisée).
    alt = prepa.apprendre(app, variables, config.VARIABLES_BORNEES,
                          config.SEUIL_ASYMETRIE_LOG, (0.01, 0.99))
    n_alt = int(prepa.ecretages(app, alt).any(axis=1).sum())

    def nb_variables(ec):
        n = ec.sum(axis=1)
        return [int((n == 0).sum()), int((n == 1).sum()), int((n == 2).sum()), int((n >= 3).sum())]

    md = [
        "# Préparation des variables : avant / après", "",
        "Rapport généré par `scripts/preparer.py`. Paramètres appris sur les "
        f"{fmt(len(app), 0)} clients d'apprentissage (80 %) seulement, enregistrés dans "
        "`models/preparation.json`, puis réappliqués tels quels aux "
        f"{fmt(len(cote), 0)} clients mis de côté (20 %). Ordre : log → écrêtage → "
        "standardisation. Règles fixées avant tout segment (voir `docs/CHOIX.md`).", "",
        f"État : {etat}.", "",
        "## 1. Règle du log", "",
        f"`log(1 + x)` pour une variable positive et sans borne haute, si son asymétrie dépasse "
        f"{config.SEUIL_ASYMETRIE_LOG:g} et si le log la réduit.", "",
        tableau(["variable", "asymétrie brute", "asymétrie après log", "log", "raison"],
                [[NOMS[v], fmt(p[v]["asymetrie_brute"]),
                  "—" if p[v]["asymetrie_log"] is None else fmt(p[v]["asymetrie_log"]),
                  "oui" if p[v]["log"] else "non", p[v]["raison"]] for v in variables]),
        "", "## 2. Seuils d'écrêtage (0,5e et 99,5e centiles, appris sur les 80 %)", "",
        "Seuils ramenés dans l'unité d'origine. Clients touchés = clients d'apprentissage.", "",
        tableau(["variable", "seuil bas", "seuil haut", "touchés en bas", "touchés en haut"],
                [[NOMS[v], fmt(unites[v][0]), fmt(unites[v][1]),
                  int((prepa.transformer(app, prep)[v] < p[v]["bas"]).sum()),
                  int((prepa.transformer(app, prep)[v] > p[v]["haut"]).sum())]
                 for v in variables]),
        "", "## 3. Clients écrêtés sur au moins une variable", "",
        tableau(["groupe", "clients", "écrêtés (≥ 1 variable)", "%"], [
            ["apprentissage (80 %)", fmt(len(app), 0), fmt(ind_app["ecrete"].sum(), 0),
             fmt(100 * ind_app["ecrete"].mean())],
            ["mis de côté (20 %)", fmt(len(cote), 0), fmt(ind_cote["ecrete"].sum(), 0),
             fmt(100 * ind_cote["ecrete"].mean())],
        ]), "",
        tableau(["groupe", "0 variable", "1 variable", "2 variables", "3 ou plus"],
                [["80 %"] + [fmt(x, 0) for x in nb_variables(ec_app)],
                 ["20 %"] + [fmt(x, 0) for x in nb_variables(ec_cote)]]), "",
        f"Pour comparaison (option écartée) : à 1 / 99, {fmt(n_alt, 0)} clients d'apprentissage "
        f"({fmt(100 * n_alt / len(app))} %) auraient été écrêtés sur au moins une variable.",
        "", "## 4. Après préparation", "",
        "Sur les 80 %, chaque variable doit avoir une moyenne de 0 et un écart-type de 1 "
        "(par construction). Sur les 20 %, des valeurs proches de 0 et 1 montrent que les "
        "paramètres se transposent bien à des clients jamais vus.", "",
        tableau(["variable", "asymétrie après", "moyenne 80 %", "écart-type 80 %",
                 "moyenne 20 %", "écart-type 20 %"],
                [[NOMS[v], fmt(z_app[v].skew()), fmt(z_app[v].mean(), 3),
                  fmt(z_app[v].std(ddof=0), 3), fmt(z_cote[v].mean(), 3),
                  fmt(z_cote[v].std(ddof=0), 3)] for v in variables]),
        "",
    ]
    rapport = config.DOSSIER_RAPPORTS / "preparation.md"
    rapport.write_text("\n".join(md), encoding="utf-8", newline="\n")

    dossier = config.RACINE / "captures_brutes"
    dossier.mkdir(exist_ok=True)
    figure(app, z_app, prep, dossier / "preparation_avant_apres.png")
    print(f"Préparation : {etat}")
    print("Rapport : reports/preparation.md ; graphique : captures_brutes/preparation_avant_apres.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
