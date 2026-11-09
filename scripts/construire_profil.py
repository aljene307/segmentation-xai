"""Construit le profil client, met 20 % des clients de côté et écrit le rapport de résumé.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\construire_profil.py

Sorties :
    data/processed/profils_apprentissage.csv  (80 %, non versionné)
    data/processed/profils_mise_de_cote.csv   (20 %, non versionné)
    docs/tirage_empreinte.json                (versionné : prouve que le tirage ne change pas)
    reports/profil_clients.md                 (versionné : comptes et statistiques agrégés)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402
from segmentation.donnees import charger_tables  # noqa: E402
from segmentation.profil import commandes_retenues, construire_profil  # noqa: E402
from segmentation.telechargement import ecrire_json  # noqa: E402
from segmentation.tirage import empreinte, separer  # noqa: E402

NOMS = {
    "recence_j": "Récence (jours)",
    "frequence": "Fréquence (commandes)",
    "montant_rs": "Montant (R$, prix des articles)",
    "part_frais_port": "Part des frais de port",
    "mensualites_moy": "Mensualités moyennes",
    "articles_par_commande": "Articles par commande",
    "delai_livraison_moy_j": "Délai de livraison moyen (jours)",
    "ecart_prevision_moy_j": "Écart moyen à la date promise (jours)",
}


def fmt(v, d=2):
    if isinstance(v, (int,)) or (isinstance(v, float) and d == 0):
        return f"{v:,.0f}".replace(",", " ")
    return f"{v:,.{d}f}".replace(",", " ")


def tableau(entetes, lignes):
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    return "\n".join(out + ["| " + " | ".join(map(str, l)) + " |" for l in lignes])


def repartition(a: pd.Series, b: pd.Series, n: int = 6) -> list[list]:
    pa, pb = a.value_counts(normalize=True) * 100, b.value_counts(normalize=True) * 100
    return [[k, fmt(pa.get(k, 0), 1), fmt(pb.get(k, 0), 1)] for k in pa.index[:n]]


def verifier_ou_ecrire_empreinte(n_app: int, cote: list[str]) -> str:
    actuelle = {"graine": config.GRAINE, "part_mise_de_cote": config.PART_MISE_DE_COTE,
                "clients_apprentissage": n_app, "clients_mise_de_cote": len(cote),
                "sha256_mise_de_cote": empreinte(cote)}
    if config.EMPREINTE_TIRAGE.exists():
        ref = json.loads(config.EMPREINTE_TIRAGE.read_text(encoding="utf-8"))
        if ref != actuelle:
            raise SystemExit("ÉCART : le tirage ne correspond plus à docs/tirage_empreinte.json")
        return "identique à l'empreinte enregistrée"
    ecrire_json(config.EMPREINTE_TIRAGE, actuelle)
    return "empreinte enregistrée (premier tirage)"


def main() -> int:
    proteger_sorties()
    tables = charger_tables(sauf=("geolocalisation",))
    profil = construire_profil(tables)
    n_commandes = len(commandes_retenues(tables, config.DEBUT_ACHATS, config.FIN_ACHATS))

    app_ids, cote_ids = separer(profil.index, config.PART_MISE_DE_COTE, config.GRAINE)
    etat_tirage = verifier_ou_ecrire_empreinte(len(app_ids), cote_ids)
    app, cote = profil.loc[app_ids], profil.loc[cote_ids]

    config.DOSSIER_PROCESSED.mkdir(parents=True, exist_ok=True)
    for df, chemin in ((app, config.PROFILS_APPRENTISSAGE), (cote, config.PROFILS_MISE_DE_COTE)):
        df.to_csv(chemin, encoding="utf-8", lineterminator="\n")

    v = config.VARIABLES_PROFIL
    ecart_type = profil[v].std()
    lignes_stats = []
    for c in v:
        a, b = app[c], cote[c]
        lignes_stats.append([NOMS[c], fmt(a.median()), fmt(b.median()), fmt(a.mean()),
                             fmt(b.mean()), fmt(abs(a.mean() - b.mean()) / ecart_type[c], 3)])

    def quantiles(df):
        q = df[v].quantile([0, 0.25, 0.5, 0.75, 0.99, 1]).T
        return [[NOMS[c]] + [fmt(x) for x in q.loc[c]] for c in v]

    recurrent = lambda df: 100 * (df["frequence"] > 1).mean()  # noqa: E731

    md = [
        "# Profil client : résumé", "",
        "Rapport généré par `scripts/construire_profil.py`. Une ligne par vrai client "
        "(`customer_unique_id`). Commandes livrées avec date de livraison, achetées du "
        f"{config.DEBUT_ACHATS} au 2018-06-30 ; Récence comptée à partir du "
        f"{config.DATE_REFERENCE}. Montants en R$. Aucune donnée d'avis utilisée.", "",
        "## Effectifs", "",
        tableau(["mesure", "valeur"], [
            ["commandes retenues", fmt(n_commandes)],
            ["clients (profils)", fmt(len(profil))],
            ["apprentissage (80 %)", fmt(len(app))],
            ["mis de côté (20 %)", fmt(len(cote))],
            ["clients en commun entre les deux groupes", len(set(app_ids) & set(cote_ids))],
            ["valeurs manquantes dans les 8 variables", int(profil[v].isna().sum().sum())],
            ["tirage", etat_tirage],
        ]), "",
        "## Statistiques des 8 variables (apprentissage, 80 %)", "",
        tableau(["variable", "min", "Q1", "médiane", "Q3", "99e centile", "max"], quantiles(app)),
        "", "## Comparaison des 80 % et des 20 %", "",
        "Écart standardisé = |moyenne 80 % − moyenne 20 %| / écart-type sur tous les clients. "
        "En dessous de 0,1, la différence est négligeable.", "",
        tableau(["variable", "médiane 80 %", "médiane 20 %", "moyenne 80 %", "moyenne 20 %",
                 "écart standardisé"], lignes_stats), "",
        tableau(["mesure", "80 %", "20 %"], [
            ["clients à plusieurs commandes (%)", fmt(recurrent(app)), fmt(recurrent(cote))],
            ["clients livrés en retard en moyenne (écart moyen > 0) (%)",
             fmt(100 * (app["ecart_prevision_moy_j"] > 0).mean()),
             fmt(100 * (cote["ecart_prevision_moy_j"] > 0).mean())],
        ]), "",
        "## Colonnes de description (jamais dans le clustering)", "",
        "**État** (6 premiers, % des clients)", "",
        tableau(["État", "80 %", "20 %"], repartition(app["etat"], cote["etat"])), "",
        "**Moyen de paiement principal** (% des clients)", "",
        tableau(["moyen", "80 %", "20 %"],
                repartition(app["paiement_principal"], cote["paiement_principal"])), "",
        "**Catégorie principale** (6 premières, % des clients)", "",
        tableau(["catégorie", "80 %", "20 %"],
                repartition(app["categorie_principale"], cote["categorie_principale"])), "",
        f"Catégories distinctes : {profil['categorie_principale'].nunique()} "
        f"(dont « {config.CATEGORIE_INCONNUE} » : "
        f"{fmt(100 * (profil['categorie_principale'] == config.CATEGORIE_INCONNUE).mean())} %).",
        "",
    ]
    sortie = config.DOSSIER_RAPPORTS / "profil_clients.md"
    sortie.write_text("\n".join(md), encoding="utf-8", newline="\n")
    print(f"Profils : {len(app)} (apprentissage) + {len(cote)} (mis de côté) ; tirage {etat_tirage}")
    print("Rapport : reports/profil_clients.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
