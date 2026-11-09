"""Évaluation finale : mesures sur un groupe de clients et verdicts des attentes E1 à E12.

Les attentes et leurs seuils sont ceux écrits et poussés dans docs/CHOIX.md avant l'ouverture
des avis des 20 %. Les mêmes fonctions mesurent les 80 % (référence) et les 20 %.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score

from segmentation import explication as X


def exiger_fichiers(chemins) -> None:
    """Arrête proprement (message clair) si un fichier produit par la reproduction manque."""
    manquants = [str(c) for c in chemins if not c.exists()]
    if manquants:
        liste = "".join(f"\n  - {m}" for m in manquants)
        raise SystemExit(
            f"Fichiers de la reproduction absents :{liste}\n"
            "Lancer d'abord les étapes 1 à 12 du README (téléchargement des données et "
            "calculs, environ une heure), puis relancer cette commande.")


def mesurer(z: pd.DataFrame, prof: pd.DataFrame, seg: pd.Series, notes: pd.DataFrame,
            plusieurs_vendeurs: pd.Series, centres: np.ndarray, seuils: list[float],
            arbre: dict, echantillon_silhouette: list, variables: list[str]) -> dict:
    """Toutes les mesures d'un groupe. `notes` : note_client (index = clients avec avis)."""
    k = len(centres)
    parts = seg.value_counts(normalize=True).reindex(range(k), fill_value=0)
    diag = X.diagnostic(z[variables].to_numpy(dtype=float), centres, seuils)
    diag.index = z.index
    sil = silhouette_score(z.loc[echantillon_silhouette, variables].to_numpy(dtype=float),
                           seg.loc[echantillon_silhouette].to_numpy())
    fid = float((X.predire_arbre(arbre, prof) == seg.loc[prof.index].to_numpy()).mean())

    avec = notes.index.intersection(seg.index)
    sat = notes.loc[avec, "satisfait"].astype(bool)
    s_avec = seg.loc[avec]
    sat_seg = sat.groupby(s_avec).mean().reindex(range(k))
    retard = prof.loc[avec, "ecart_prevision_moy_j"] > 0
    dans_s3 = s_avec == 3
    pv = plusieurs_vendeurs.reindex(avec).fillna(False).astype(bool)
    return {
        "clients": int(len(seg)),
        "parts": [float(p) for p in parts],
        "silhouette": float(sil),
        "atypiques": float(diag["atypique"].mean()),
        "atypiques_par_segment": [float(diag.loc[diag["segment"] == s, "atypique"].mean())
                                  for s in range(k)],
        "frontiere": float(diag["frontiere"].mean()),
        "fidelite_arbre": fid,
        "clients_avec_avis": int(len(avec)),
        "sans_avis": float(1 - len(avec) / len(seg)),
        "satisfaits": float(sat.mean()),
        "satisfaits_par_segment": [float(x) for x in sat_seg],
        "clients_avec_avis_par_segment": [int((s_avec == s).sum()) for s in range(k)],
        "ordre_satisfaction": [int(s) for s in sat_seg.sort_values(ascending=False).index],
        "ari": float(adjusted_rand_score(sat.astype(int), s_avec)),
        "nmi": float(normalized_mutual_info_score(sat.astype(int), s_avec)),
        "satisfaits_a_l_heure": float(sat[~retard].mean()),
        "satisfaits_en_retard": float(sat[retard].mean()),
        "ecart_retard": float(sat[~retard].mean() - sat[retard].mean()),
        "s3_plusieurs_vendeurs": int((dans_s3 & pv).sum()),
        "s3_un_vendeur": int((dans_s3 & ~pv).sum()),
        "s3_ecart": float(sat[dans_s3 & pv].mean() - sat[dans_s3 & ~pv].mean()),
    }


def verdicts(r: dict, m: dict) -> list[dict]:
    """r : mesures des 80 % (référence) ; m : mesures des 20 %. Seuils = docs/CHOIX.md."""
    k = len(r["parts"])
    pt = 100  # proportions en points de pourcentage
    v = []

    def ajouter(code, mesure, ref, val, seuil, ok, statut):
        v.append({"code": code, "mesure": mesure, "valeur_80": ref, "valeur_20": val,
                  "attente": seuil, "atteinte": bool(ok), "statut": statut})

    ecarts_parts = [abs(m["parts"][s] - r["parts"][s]) * pt for s in range(k)]
    ajouter("E1", "part de chaque segment (%)", [round(p * pt, 2) for p in r["parts"]],
            [round(p * pt, 2) for p in m["parts"]], "écart ≤ 1,0 point par segment",
            max(ecarts_parts) <= 1.0, "inédit")
    ajouter("E2", "silhouette (8 000 clients)", round(r["silhouette"], 4),
            round(m["silhouette"], 4), "écart ≤ 0,02",
            abs(m["silhouette"] - r["silhouette"]) <= 0.02, "inédit")
    ajouter("E3", "atypiques (%) : total ; par segment", round(r["atypiques"] * pt, 2),
            [round(m["atypiques"] * pt, 2)] + [round(a * pt, 2) for a in m["atypiques_par_segment"]],
            "total entre 4,0 et 6,0 % ; chaque segment entre 3,0 et 7,0 %",
            4.0 <= m["atypiques"] * pt <= 6.0
            and all(3.0 <= a * pt <= 7.0 for a in m["atypiques_par_segment"]), "déjà observé")
    ajouter("E4", "clients à la frontière (%)", round(r["frontiere"] * pt, 2),
            round(m["frontiere"] * pt, 2), "écart ≤ 1,5 point",
            abs(m["frontiere"] - r["frontiere"]) * pt <= 1.5, "déjà observé")
    ajouter("E5", "fidélité de l'arbre (%)", round(r["fidelite_arbre"] * pt, 2),
            round(m["fidelite_arbre"] * pt, 2), "au moins 85 % et écart ≤ 2 points",
            m["fidelite_arbre"] * pt >= 85
            and abs(m["fidelite_arbre"] - r["fidelite_arbre"]) * pt <= 2, "déjà observé")
    ajouter("E6", "clients sans avis (%)", round(r["sans_avis"] * pt, 2),
            round(m["sans_avis"] * pt, 2), "au plus 1,5 %", m["sans_avis"] * pt <= 1.5, "inédit")
    ajouter("E7", "satisfaits, tous segments (%)", round(r["satisfaits"] * pt, 2),
            round(m["satisfaits"] * pt, 2), "écart ≤ 2 points",
            abs(m["satisfaits"] - r["satisfaits"]) * pt <= 2, "inédit")
    limites = [3, 3, 3, 3, 5]
    ajouter("E8", "satisfaits par segment (%)",
            [round(x * pt, 2) for x in r["satisfaits_par_segment"]],
            [round(x * pt, 2) for x in m["satisfaits_par_segment"]],
            "écart ≤ 3 points (S0 à S3), ≤ 5 points (S4)",
            all(abs(m["satisfaits_par_segment"][s] - r["satisfaits_par_segment"][s]) * pt
                <= limites[s] for s in range(k)), "inédit")
    o = m["ordre_satisfaction"]
    ajouter("E9", "ordre des segments (du plus au moins satisfait)",
            [f"S{s}" for s in r["ordre_satisfaction"]], [f"S{s}" for s in o],
            "S2 dernier, S3 avant-dernier ; S0 et S1 ≥ 80 %",
            o[-1] == 2 and o[-2] == 3 and m["satisfaits_par_segment"][0] * pt >= 80
            and m["satisfaits_par_segment"][1] * pt >= 80, "inédit")
    ajouter("E10", "ARI ; NMI", [round(r["ari"], 4), round(r["nmi"], 4)],
            [round(m["ari"], 4), round(m["nmi"], 4)], "ARI entre 0,04 et 0,10 ; NMI entre 0,02 et 0,06",
            0.04 <= m["ari"] <= 0.10 and 0.02 <= m["nmi"] <= 0.06, "inédit")
    ajouter("E11", "satisfaits à l'heure moins en retard (points)", round(r["ecart_retard"] * pt, 2),
            round(m["ecart_retard"] * pt, 2), "au moins 40 points",
            m["ecart_retard"] * pt >= 40, "inédit")
    ajouter("E12", "S3 : plusieurs vendeurs moins un seul (points)", round(r["s3_ecart"] * pt, 2),
            round(m["s3_ecart"] * pt, 2), "au plus −10 points",
            m["s3_ecart"] * pt <= -10, "inédit")
    return v
