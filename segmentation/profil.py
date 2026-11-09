"""Profil client : une ligne par vrai client (`customer_unique_id`).

Chaque valeur d'un client ne dépend que de ses propres commandes : ce calcul
n'apprend rien sur l'ensemble des clients et peut donc être fait avant le tirage
des 20 % mis de côté. Aucune donnée d'avis n'est utilisée. Montants en R$.
"""

from __future__ import annotations

import pandas as pd

from segmentation import config
from segmentation.exploration import dans_periode, table_commandes


def commandes_retenues(tables: dict[str, pd.DataFrame], debut: str, fin: str) -> pd.DataFrame:
    """Commandes livrées (avec date) achetées dans [debut, fin[, une ligne par commande."""
    t = dans_periode(table_commandes(tables), debut, fin).copy()
    # 2 lignes de paiement ont 0 mensualité : un paiement se fait au moins en 1 fois.
    t["mensualites"] = t["mensualites"].fillna(1).clip(lower=1)
    return t


def _principal(df: pd.DataFrame, cle: str, valeur: str, poids: str) -> pd.Series:
    """Pour chaque `cle`, la `valeur` qui pèse le plus (somme de `poids`) ;
    en cas d'égalité, la première par ordre alphabétique (résultat reproductible)."""
    s = df.groupby([cle, valeur])[poids].sum().reset_index()
    s = s.sort_values([cle, poids, valeur], ascending=[True, False, True])
    return s.drop_duplicates(cle).set_index(cle)[valeur]


def categories_par_commande(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Prix par (commande, catégorie anglaise), catégorie manquante = « inconnue »."""
    trad = dict(zip(tables["traduction_categories"]["product_category_name"],
                    tables["traduction_categories"]["product_category_name_english"]))
    trad.update(config.TRADUCTIONS_AJOUTEES)
    art = tables["articles"].merge(
        tables["produits"][["product_id", "product_category_name"]], on="product_id", how="left"
    )
    art["categorie"] = (art["product_category_name"].map(trad)
                        .fillna(config.CATEGORIE_INCONNUE))
    return art[["order_id", "categorie", "price"]]


def construire_profil(
    tables: dict[str, pd.DataFrame],
    debut: str = config.DEBUT_ACHATS,
    fin: str = config.FIN_ACHATS,
    date_reference: str = config.DATE_REFERENCE,
) -> pd.DataFrame:
    t = commandes_retenues(tables, debut, fin)
    ref = pd.Timestamp(date_reference)
    g = t.groupby("customer_unique_id")

    prix = g["montant_articles"].sum()
    frais = g["frais_port"].sum()
    dernier_achat = g["order_purchase_timestamp"].max()

    profil = pd.DataFrame({
        "recence_j": (ref - dernier_achat.dt.normalize()).dt.days,
        "frequence": g.size(),
        "montant_rs": prix,
        "part_frais_port": frais / (prix + frais),
        "mensualites_moy": g["mensualites"].mean(),
        "articles_par_commande": g["nb_articles"].mean(),
        "delai_livraison_moy_j": g["delai_livraison_j"].mean(),
        "ecart_prevision_moy_j": g["ecart_prevision_j"].mean(),
    })

    # Colonnes de description (jamais dans le clustering).
    profil["etat"] = (t.sort_values("order_purchase_timestamp")
                      .groupby("customer_unique_id")["customer_state"].last())
    cat = categories_par_commande(tables).merge(
        t[["customer_unique_id"]], left_on="order_id", right_index=True)
    profil["categorie_principale"] = _principal(cat, "customer_unique_id", "categorie", "price")
    pai = tables["paiements"].merge(
        t[["customer_unique_id"]], left_on="order_id", right_index=True)
    profil["paiement_principal"] = _principal(
        pai, "customer_unique_id", "payment_type", "payment_value")
    profil["premier_achat"] = g["order_purchase_timestamp"].min().dt.date

    profil.index.name = "customer_unique_id"
    return profil.sort_index()[config.VARIABLES_PROFIL + config.COLONNES_DESCRIPTION]
