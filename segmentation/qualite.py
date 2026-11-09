"""Contrôles qualité des tables Olist.

Chaque fonction renvoie des comptes agrégés (jamais de lignes individuelles),
pour que le rapport puisse être versionné sans exposer de données.
"""

from __future__ import annotations

import pandas as pd

TOLERANCE_RS = 0.01  # écart toléré, en R$, entre paiements et articles d'une commande


def resume_table(df: pd.DataFrame, cles: list[str] | None = None) -> dict:
    """Lignes, colonnes, doublons exacts et doublons de clé."""
    res = {
        "lignes": len(df),
        "colonnes": df.shape[1],
        "doublons_exacts": int(df.duplicated().sum()),
    }
    if cles:
        res["cle"] = " + ".join(cles)
        res["doublons_cle"] = int(df.duplicated(subset=cles).sum())
    return res


def manquants(df: pd.DataFrame) -> pd.DataFrame:
    """Valeurs manquantes par colonne (seulement les colonnes concernées)."""
    n = df.isna().sum()
    n = n[n > 0]
    return pd.DataFrame({"manquants": n, "pct": (100 * n / len(df)).round(2)})


def orphelins(enfant: pd.Series, parent: pd.Series) -> int:
    """Nombre de valeurs (non manquantes) de `enfant` absentes de `parent`."""
    e = enfant.dropna()
    return int((~e.isin(set(parent.dropna()))).sum())


def sans_correspondance(parent: pd.Series, enfant: pd.Series) -> int:
    """Nombre de valeurs distinctes de `parent` jamais référencées dans `enfant`."""
    return int((~parent.drop_duplicates().isin(set(enfant.dropna()))).sum())


def controles_dates(commandes: pd.DataFrame) -> dict:
    """Incohérences de chronologie et de statut sur les commandes."""
    c = commandes
    achat = c["order_purchase_timestamp"]
    livre = c["order_delivered_customer_date"]
    delivered = c["order_status"] == "delivered"
    return {
        "achat_min": achat.min(),
        "achat_max": achat.max(),
        "validation_avant_l_achat": int((c["order_approved_at"] < achat).sum()),
        "remise_au_transporteur_avant_l_achat": int((c["order_delivered_carrier_date"] < achat).sum()),
        "livraison_avant_l_achat": int((livre < achat).sum()),
        "livraison_avant_remise_au_transporteur": int(
            (livre < c["order_delivered_carrier_date"]).sum()
        ),
        "livrées_sans_date_de_livraison": int((delivered & livre.isna()).sum()),
        "non_livrées_avec_date_de_livraison": int((~delivered & livre.notna()).sum()),
        "livrées_en_retard": int((delivered & (livre.dt.normalize()
                                  > c["order_estimated_delivery_date"])).sum()),
        "livrées": int(delivered.sum()),
    }


def controles_montants(articles: pd.DataFrame, paiements: pd.DataFrame) -> dict:
    """Montants nuls ou négatifs, et cohérence paiements / articles par commande (R$)."""
    total_articles = (articles["price"] + articles["freight_value"]).groupby(
        articles["order_id"]
    ).sum()
    total_paiements = paiements.groupby("order_id")["payment_value"].sum()
    communs = total_articles.index.intersection(total_paiements.index)
    ecart = (total_paiements[communs] - total_articles[communs]).abs()
    return {
        "prix_nul_ou_négatif": int((articles["price"] <= 0).sum()),
        "frais_de_port_négatifs": int((articles["freight_value"] < 0).sum()),
        "frais_de_port_nuls": int((articles["freight_value"] == 0).sum()),
        "paiement_nul_ou_négatif": int((paiements["payment_value"] <= 0).sum()),
        "nombre_de_mensualités_égal_à_0": int((paiements["payment_installments"] == 0).sum()),
        "commandes_comparées": len(communs),
        "commandes_avec_écart_paiements_articles_>_0,01_R$": int((ecart > TOLERANCE_RS).sum()),
        "écart_médian_quand_écart_(R$)": float(ecart[ecart > TOLERANCE_RS].median())
        if (ecart > TOLERANCE_RS).any() else 0.0,
    }


def commandes_par_client(clients: pd.DataFrame, commandes: pd.DataFrame) -> pd.Series:
    """Nombre de commandes par vrai client (`customer_unique_id`)."""
    lien = commandes[["order_id", "customer_id"]].merge(
        clients[["customer_id", "customer_unique_id"]], on="customer_id", how="left"
    )
    return lien.groupby("customer_unique_id")["order_id"].nunique()


def controles_avis(avis: pd.DataFrame, commandes: pd.DataFrame) -> dict:
    """Structure de la table des avis (utilisée seulement pour l'évaluation)."""
    par_commande = avis.groupby("order_id")["review_id"].nunique()
    return {
        "avis": len(avis),
        "review_id_distincts": int(avis["review_id"].nunique()),
        "review_id_sur_plusieurs_commandes": int(
            (avis.groupby("review_id")["order_id"].nunique() > 1).sum()
        ),
        "commandes_avec_avis": int(par_commande.size),
        "commandes_avec_plusieurs_avis": int((par_commande > 1).sum()),
        "commandes_sans_avis": sans_correspondance(commandes["order_id"], avis["order_id"]),
        "avis_orphelins": orphelins(avis["order_id"], commandes["order_id"]),
        "repartition_notes": avis["review_score"].value_counts().sort_index().to_dict(),
    }
