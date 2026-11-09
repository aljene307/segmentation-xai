"""Règle de choix de k, telle qu'écrite et poussée dans docs/CHOIX.md avant tout calcul.

1. admissibilité : (a) plus petit segment ≥ 2 % ; (b) ARI bootstrap moyen ≥ 0,80 ;
   (c) Jaccard moyen de chaque segment ≥ 0,60 ;
2. parmi les admissibles : rangs de la silhouette (haute = 1), de Calinski-Harabasz
   (haut = 1) et de Davies-Bouldin (bas = 1) ; la plus petite somme gagne ; égalité :
   le plus petit k ;
3. si aucun k n'est admissible : parmi ceux qui respectent (a), le meilleur ARI moyen
   (égalité : le plus petit k).
Le refus métier (règle 4) n'est pas automatisé : il relève d'une décision écrite.
"""

from __future__ import annotations

import pandas as pd

PART_MIN = 0.02
ARI_MIN = 0.80
JACCARD_MIN = 0.60


def admissibilite(t: pd.DataFrame) -> pd.DataFrame:
    """t indexé par k, colonnes : plus_petit_pct, ari_boot_moyen, jaccard_min."""
    r = pd.DataFrame(index=t.index)
    r["a_taille"] = t["plus_petit_pct"] >= 100 * PART_MIN
    r["b_ari"] = t["ari_boot_moyen"] >= ARI_MIN
    r["c_jaccard"] = t["jaccard_min"] >= JACCARD_MIN
    r["admissible"] = r[["a_taille", "b_ari", "c_jaccard"]].all(axis=1)
    return r


def rangs(t: pd.DataFrame) -> pd.DataFrame:
    """Rangs (1 = meilleur) et somme, sur les k fournis. Ex æquo : même rang (le plus petit)."""
    r = pd.DataFrame(index=t.index)
    r["rang_silhouette"] = t["silhouette"].rank(ascending=False, method="min").astype(int)
    r["rang_calinski_harabasz"] = t["calinski_harabasz"].rank(ascending=False,
                                                              method="min").astype(int)
    r["rang_davies_bouldin"] = t["davies_bouldin"].rank(ascending=True, method="min").astype(int)
    r["somme"] = r.sum(axis=1)
    return r


def choisir_k(t: pd.DataFrame) -> dict:
    adm = admissibilite(t)
    admissibles = adm.index[adm["admissible"]]
    if len(admissibles):
        r = rangs(t.loc[admissibles])
        k = int(min(r.index[r["somme"] == r["somme"].min()]))  # égalité : le plus petit k
        return {"k": k, "voie": "règle 3 (somme des rangs parmi les admissibles)",
                "admissibilite": adm, "rangs": r}
    taille_ok = adm.index[adm["a_taille"]]
    if not len(taille_ok):
        raise ValueError("Aucun k ne respecte la taille minimale : cas non prévu par la règle.")
    ari = t.loc[taille_ok, "ari_boot_moyen"]
    k = int(min(ari.index[ari == ari.max()]))
    return {"k": k, "voie": "règle 5 (aucun k admissible : meilleur ARI parmi les tailles valides)",
            "admissibilite": adm, "rangs": None}
