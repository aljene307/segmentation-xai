"""Tests des fonctions de contrôle qualité sur de petites tables construites à la main."""

import pandas as pd

from segmentation import qualite as q


def test_resume_table_doublons():
    df = pd.DataFrame({"id": [1, 1, 2, 2], "v": [10, 10, 20, 21]})
    r = q.resume_table(df, ["id"])
    assert r == {"lignes": 4, "colonnes": 2, "doublons_exacts": 1,
                 "cle": "id", "doublons_cle": 2}


def test_manquants_ne_liste_que_les_colonnes_touchees():
    df = pd.DataFrame({"a": [1, None, 3, None], "b": [1, 2, 3, 4]})
    m = q.manquants(df)
    assert list(m.index) == ["a"]
    assert m.loc["a", "manquants"] == 2 and m.loc["a", "pct"] == 50.0


def test_orphelins_et_sans_correspondance():
    parent = pd.Series(["A", "B", "C"])
    enfant = pd.Series(["A", "A", "D", None])
    assert q.orphelins(enfant, parent) == 1           # D
    assert q.sans_correspondance(parent, enfant) == 2  # B et C


def _commandes():
    t = pd.Timestamp
    return pd.DataFrame({
        "order_status": ["delivered", "delivered", "canceled"],
        "order_purchase_timestamp": [t("2018-01-10"), t("2018-01-10"), t("2018-01-10")],
        "order_approved_at": [t("2018-01-10 01:00"), t("2018-01-09"), pd.NaT],
        "order_delivered_carrier_date": [t("2018-01-11"), t("2018-01-12"), pd.NaT],
        "order_delivered_customer_date": [t("2018-01-15 18:00"), pd.NaT, t("2018-01-20")],
        "order_estimated_delivery_date": [t("2018-01-14"), t("2018-01-20"), t("2018-01-20")],
    })


def test_controles_dates():
    d = q.controles_dates(_commandes())
    assert d["validation_avant_l_achat"] == 1
    assert d["livrées_sans_date_de_livraison"] == 1
    assert d["non_livrées_avec_date_de_livraison"] == 1
    assert d["livrées_en_retard"] == 1   # livrée le 15, prévue le 14
    assert d["livrées"] == 2


def test_controles_montants_ecart_paiement():
    articles = pd.DataFrame({"order_id": ["o1", "o1", "o2"], "price": [10.0, 5.0, 20.0],
                             "freight_value": [2.0, 0.0, 3.0]})
    paiements = pd.DataFrame({"order_id": ["o1", "o2"], "payment_value": [17.0, 30.0],
                              "payment_installments": [1, 0]})
    m = q.controles_montants(articles, paiements)
    assert m["commandes_comparées"] == 2
    assert m["commandes_avec_écart_paiements_articles_>_0,01_R$"] == 1  # o2 : 30 contre 23
    assert m["écart_médian_quand_écart_(R$)"] == 7.0
    assert m["frais_de_port_nuls"] == 1
    assert m["nombre_de_mensualités_égal_à_0"] == 1


def test_commandes_par_client_regroupe_les_customer_id():
    clients = pd.DataFrame({"customer_id": ["c1", "c2", "c3"],
                            "customer_unique_id": ["U", "U", "V"]})
    commandes = pd.DataFrame({"order_id": ["o1", "o2", "o3"],
                              "customer_id": ["c1", "c2", "c3"]})
    n = q.commandes_par_client(clients, commandes)
    assert n.to_dict() == {"U": 2, "V": 1}
