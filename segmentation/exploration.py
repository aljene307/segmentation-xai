"""Tables d'exploration : commandes livrées, comptes par mois, par État, valeurs extrêmes.

Aucune colonne d'avis n'est utilisée ici. Montants en R$.
"""

from __future__ import annotations

import pandas as pd

JOUR = pd.Timedelta(days=1)


def commandes_livrees(commandes: pd.DataFrame) -> pd.DataFrame:
    """Commandes au statut « delivered » ET avec une date de livraison au client."""
    ok = (commandes["order_status"] == "delivered") & commandes[
        "order_delivered_customer_date"
    ].notna()
    return commandes[ok]


def clients_sans_commande_livree(
    clients: pd.DataFrame, commandes: pd.DataFrame
) -> dict:
    """Vrais clients (`customer_unique_id`) qui disparaissent si l'on ne garde que les livrées."""
    uid = clients.set_index("customer_id")["customer_unique_id"]
    tous = set(uid[commandes["customer_id"]])
    gardes = set(uid[commandes_livrees(commandes)["customer_id"]])
    return {"clients": len(tous), "gardes": len(gardes), "perdus": len(tous - gardes)}


def table_commandes(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Une ligne par commande livrée, avec les variables brutes à explorer."""
    cmd = commandes_livrees(tables["commandes"])
    art = tables["articles"]
    pai = tables["paiements"]
    par_cmd = art.groupby("order_id").agg(
        montant_articles=("price", "sum"),
        frais_port=("freight_value", "sum"),
        nb_articles=("order_item_id", "count"),
        nb_vendeurs=("seller_id", "nunique"),
    )
    mens = pai.groupby("order_id")["payment_installments"].max().rename("mensualites")
    uid = tables["clients"].set_index("customer_id")[["customer_unique_id", "customer_state"]]
    t = (
        cmd.set_index("order_id")
        .join(par_cmd, how="inner")
        .join(mens, how="left")
        .join(uid, on="customer_id")
    )
    t["delai_livraison_j"] = (
        t["order_delivered_customer_date"] - t["order_purchase_timestamp"]
    ) / JOUR
    t["ecart_prevision_j"] = (
        t["order_delivered_customer_date"].dt.normalize() - t["order_estimated_delivery_date"]
    ) / JOUR
    t["mois"] = t["order_purchase_timestamp"].dt.to_period("M")
    return t


def commandes_par_mois(commandes: pd.DataFrame) -> pd.DataFrame:
    """Toutes les commandes et les livrées, par mois d'achat (mois vides inclus)."""
    mois = commandes["order_purchase_timestamp"].dt.to_period("M")
    livre = commandes.index.isin(commandes_livrees(commandes).index)
    res = pd.DataFrame({"toutes": mois.value_counts(), "livrees": mois[livre].value_counts()})
    plage = pd.period_range(res.index.min(), res.index.max(), freq="M")
    return res.reindex(plage, fill_value=0).fillna(0).astype(int)


def valeurs_extremes(df: pd.DataFrame, colonnes: list[str]) -> pd.DataFrame:
    """Asymétrie et part des valeurs hors moustaches (règle de Tukey : 1,5 × écart interquartile)."""
    lignes = {}
    for c in colonnes:
        x = df[c].dropna()
        q1, q3 = x.quantile([0.25, 0.75])
        eiq = q3 - q1
        hors = ((x < q1 - 1.5 * eiq) | (x > q3 + 1.5 * eiq)).mean()
        lignes[c] = {
            "min": x.min(), "mediane": x.median(), "moyenne": x.mean(), "max": x.max(),
            "asymetrie": x.skew(), "pct_hors_moustaches": 100 * hors,
            "positive_ou_nulle": bool((x >= 0).all()),
        }
    return pd.DataFrame(lignes).T


def repartition_etats(table: pd.DataFrame) -> pd.DataFrame:
    """Clients distincts par État (un client est compté dans l'État de sa dernière commande)."""
    dernier = table.sort_values("order_purchase_timestamp").groupby("customer_unique_id").last()
    n = dernier["customer_state"].value_counts()
    return pd.DataFrame({"clients": n, "pct": (100 * n / n.sum()).round(2),
                         "pct_cumule": (100 * n.cumsum() / n.sum()).round(2)})


def effet_coupure(commandes: pd.DataFrame, table: pd.DataFrame) -> pd.DataFrame:
    """Par mois d'achat : part livrée, délais réels et délai promis, part de SP.

    Sert à repérer une coupure de l'extraction : si les livraisons lentes ne sont
    pas encore arrivées, les derniers mois montrent des délais réels plus courts
    (et, si les commandes non livrées ont été retirées, des délais promis plus
    courts et plus de clients proches, à SP)."""
    mois = commandes["order_purchase_timestamp"].dt.to_period("M")
    promis = (
        commandes["order_estimated_delivery_date"]
        - commandes["order_purchase_timestamp"].dt.normalize()
    ) / JOUR
    g = table.groupby("mois")
    res = pd.DataFrame({
        "commandes": mois.value_counts(),
        "livrees": g.size(),
        "delai_median": g["delai_livraison_j"].median(),
        "delai_p90": g["delai_livraison_j"].quantile(0.9),
        "delai_promis_median": promis.groupby(mois).median(),
        "pct_sp": 100 * g["customer_state"].apply(lambda s: (s == "SP").mean()),
    }).sort_index()
    res["pct_livrees"] = 100 * res["livrees"] / res["commandes"]
    return res.dropna(subset=["livrees"]).round(1)


def livraisons_par_semaine(commandes: pd.DataFrame, depuis: str) -> pd.Series:
    """Nombre de livraisons par semaine (lundi-dimanche) de date de livraison."""
    d = commandes_livrees(commandes)["order_delivered_customer_date"]
    return d[d >= depuis].dt.to_period("W-SUN").value_counts().sort_index()


def correlations(df: pd.DataFrame, colonnes: list[str]) -> pd.DataFrame:
    """Corrélations de Spearman : calculées sur les rangs, donc peu sensibles
    aux valeurs extrêmes et à l'asymétrie (un log ne les changerait pas)."""
    return df[colonnes].corr(method="spearman")
