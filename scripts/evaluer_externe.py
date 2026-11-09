"""Évaluation externe des segments (k = 5) avec la note d'avis, sur les 80 % seulement.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\evaluer_externe.py

Lancé après le choix de k, commité et poussé. Les avis des 20 % mis de côté ne sont
PAS lus : les avis sont filtrés aux commandes des clients d'apprentissage, et le script
s'arrête si un client mis de côté apparaît.
Sortie : reports/evaluation_externe.md (versionné).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    adjusted_rand_score,
    homogeneity_completeness_v_measure,
    normalized_mutual_info_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation import partitions as P  # noqa: E402
from segmentation.avis import note_client  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402
from segmentation.donnees import charger_avis, charger_tables  # noqa: E402
from segmentation.profil import commandes_retenues  # noqa: E402


def fmt(v, d=3):
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else \
        f"{v:,.{d}f}".replace(",", " ")


def tableau(entetes, lignes):
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    return "\n".join(out + ["| " + " | ".join(map(str, l)) + " |" for l in lignes])


def indices(segments: pd.Series, satisfait: pd.Series) -> dict:
    s = segments[segments >= 0]
    y = satisfait.reindex(s.index).dropna().astype(int)
    s = s.loc[y.index]
    h, c, v = homogeneity_completeness_v_measure(y, s)
    return {"clients": len(s), "ari": adjusted_rand_score(y, s),
            "nmi": normalized_mutual_info_score(y, s), "v": v, "homogeneite": h, "completude": c}


def main() -> int:
    proteger_sorties()
    k = config.K_RETENU
    app_ids = pd.read_csv(config.PROFILS_APPRENTISSAGE, usecols=["customer_unique_id"])[
        "customer_unique_id"]
    cote_ids = set(pd.read_csv(config.PROFILS_MISE_DE_COTE, usecols=["customer_unique_id"])[
        "customer_unique_id"])
    lab = pd.read_csv(config.PARTITIONS, index_col="customer_unique_id")
    prof = pd.read_csv(config.PROFILS_APPRENTISSAGE, index_col="customer_unique_id")

    # Commandes retenues des seuls clients d'apprentissage, puis avis de ces commandes.
    t = commandes_retenues(charger_tables(sauf=("geolocalisation",)),
                           config.DEBUT_ACHATS, config.FIN_ACHATS)
    t = t[t["customer_unique_id"].isin(set(app_ids))]
    commandes_clients = t["customer_unique_id"]
    avis = charger_avis()
    avis = avis[avis["order_id"].isin(commandes_clients.index)]
    notes = note_client(avis, commandes_clients)
    if set(notes.index) & cote_ids or set(commandes_clients) & cote_ids:
        raise SystemExit("ARRÊT : un client mis de côté apparaît dans l'évaluation.")

    seg = lab[f"kmeans_k{k}"]
    sat = notes["satisfait"]
    n_app = len(lab)
    sans = n_app - len(notes)

    # Autres méthodes au même k (comparaison seulement).
    z = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    ordre = P.ordre_echantillon(z.index, config.GRAINE)[:config.N_ECHANTILLON_CAH]
    arbre, _ = P.cah_ward(z.loc[ordre, config.VARIABLES_PROFIL].to_numpy(dtype=float))
    cah = pd.Series(P.couper(arbre, k), index=ordre)
    comparaison = {
        f"K-Means 8 variables (retenu), k = {k}": indices(seg, sat),
        f"Mixte F1–F5, k = {k}": indices(lab[f"mixte_k{k}"], sat),
        f"Mixte F1–F4 (sensibilité), k = {k}": indices(lab[f"mixte_sensibilite_k{k}"], sat),
        f"CAH de Ward 8 variables (6 000), k = {k}": indices(cah, sat),
        f"HDBSCAN F1–F5 ({lab['hdbscan'].max() + 1} groupes, bruit exclu)":
            indices(lab["hdbscan"], sat),
    }
    ref = comparaison[f"K-Means 8 variables (retenu), k = {k}"]

    # Par segment.
    df = pd.DataFrame({"segment": seg}).join(notes)
    lignes = []
    for s in range(k):
        d = df[df["segment"] == s]
        avec = d["note_client"].notna()
        lignes.append([f"S{s} {config.SEGMENTS_NOMS_ACTIONS[s][0]}", fmt(len(d), 0),
                       fmt(avec.sum(), 0), fmt(100 * (~avec).mean(), 1),
                       fmt(100 * d.loc[avec, "satisfait"].mean(), 1),
                       fmt(d["note_client"].mean(), 2),
                       fmt(100 * (d.loc[avec, "note_client"] == 1).mean(), 1)])
    tout = df["note_client"].notna()
    lignes.append(["**Tous les clients d'apprentissage**", fmt(len(df), 0), fmt(tout.sum(), 0),
                   fmt(100 * (~tout).mean(), 1), fmt(100 * df.loc[tout, "satisfait"].mean(), 1),
                   fmt(df["note_client"].mean(), 2),
                   fmt(100 * (df.loc[tout, "note_client"] == 1).mean(), 1)])

    retard = prof.loc[notes.index, "ecart_prevision_moy_j"] > 0
    md = [
        "# Évaluation externe des segments (note d'avis)", "",
        "> **À lire d'abord.** Les variables de délai (délai de livraison moyen, écart à la date "
        "promise) entrent dans le clustering, et un retard entraîne souvent une mauvaise note. "
        "Le segment **S2 « Livraison lente ou en retard »**, défini par ces variables, sera donc "
        "lié à la note **par construction** : un lien entre S2 et l'insatisfaction ne prouve pas "
        "que la segmentation « découvre » la satisfaction. Par ailleurs, avec une étiquette à "
        "deux classes et des segments de comportement, l'ARI et la NMI sont faibles par nature ; "
        "les taux par segment sont les plus parlants (écrit d'avance dans `docs/CHOIX.md`).", "",
        "Rapport généré par `scripts/evaluer_externe.py`, après le choix de k = 5 (commité et "
        "poussé). Clients d'apprentissage (80 %) seulement ; **les avis des 20 % mis de côté "
        "n'ont pas été lus**. Note du client = moyenne des notes de ses commandes retenues "
        "(avis le plus récent par commande) ; « satisfait » si la note vaut au moins 4 ; "
        "clients sans avis exclus des indices.", "",
        "## 1. Couverture", "",
        tableau(["mesure", "valeur"], [
            ["clients d'apprentissage", fmt(n_app, 0)],
            ["clients avec au moins un avis", fmt(len(notes), 0)],
            ["clients sans avis (exclus des indices)", f"{fmt(sans, 0)} ({fmt(100 * sans / n_app, 2)} %)"],
            ["clients à plusieurs commandes notées", fmt((notes['commandes_notees'] > 1).sum(), 0)],
            ["part de satisfaits (note ≥ 4)", f"{fmt(100 * sat.mean(), 1)} %"],
        ]), "",
        "## 2. Indices externes (segments retenus contre « satisfait »)", "",
        tableau(["indice", "valeur"], [
            ["ARI", fmt(ref["ari"], 4)], ["NMI", fmt(ref["nmi"], 4)],
            ["V-measure", fmt(ref["v"], 4)], ["homogénéité", fmt(ref["homogeneite"], 4)],
            ["complétude", fmt(ref["completude"], 4)]]), "",
        "- **Homogénéité** : à quel point chaque segment ne contient qu'une seule classe "
        "(satisfaits ou non).",
        "- **Complétude** : à quel point chaque classe tient dans un seul segment.",
        "- **V-measure** : moyenne harmonique des deux ; la NMI en est très proche ici.", "",
        "## 3. Par segment", "",
        tableau(["segment", "clients", "avec avis", "sans avis (%)", "satisfaits (%)",
                 "note moyenne", "note = 1 (%)"], lignes), "",
        "## 4. Le lien retard / note, mesuré directement", "",
        tableau(["clients avec avis", "clients", "satisfaits (%)", "note moyenne"], [
            ["livrés en retard en moyenne (écart > 0)", fmt(retard.sum(), 0),
             fmt(100 * sat[retard].mean(), 1), fmt(notes.loc[retard, "note_client"].mean(), 2)],
            ["livrés à l'heure ou en avance", fmt((~retard).sum(), 0),
             fmt(100 * sat[~retard].mean(), 1), fmt(notes.loc[~retard, "note_client"].mean(), 2)],
        ]), "",
        "## 5. Comparaison des méthodes au même k (information, ne change aucune décision)", "",
        tableau(["méthode", "clients avec avis", "ARI", "NMI", "V-measure", "homogénéité",
                 "complétude"],
                [[m, fmt(r["clients"], 0), fmt(r["ari"], 4), fmt(r["nmi"], 4), fmt(r["v"], 4),
                  fmt(r["homogeneite"], 4), fmt(r["completude"], 4)]
                 for m, r in comparaison.items()]), "",
    ]
    (config.DOSSIER_RAPPORTS / "evaluation_externe.md").write_text(
        "\n".join(md), encoding="utf-8", newline="\n")
    print("Rapport : reports/evaluation_externe.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
