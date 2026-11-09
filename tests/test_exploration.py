"""Tests des fonctions d'exploration sur de petites tables construites à la main."""

import pandas as pd

from segmentation import exploration as ex

T = pd.Timestamp


def _tables():
    clients = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3", "c4"],
        "customer_unique_id": ["U", "U", "V", "W"],
        "customer_state": ["SP", "RJ", "MG", "SP"],
    })
    commandes = pd.DataFrame({
        "order_id": ["o1", "o2", "o3", "o4"],
        "customer_id": ["c1", "c2", "c3", "c4"],
        "order_status": ["delivered", "delivered", "delivered", "canceled"],
        "order_purchase_timestamp": [T("2017-01-05"), T("2017-03-01"), T("2017-03-10"),
                                     T("2017-03-12")],
        "order_delivered_customer_date": [T("2017-01-10 12:00"), T("2017-03-04"), pd.NaT,
                                          pd.NaT],
        "order_estimated_delivery_date": [T("2017-01-09"), T("2017-03-10"), T("2017-03-20"),
                                          T("2017-03-20")],
    })
    articles = pd.DataFrame({
        "order_id": ["o1", "o1", "o2"], "order_item_id": [1, 2, 1],
        "seller_id": ["s1", "s2", "s1"], "price": [10.0, 30.0, 5.0],
        "freight_value": [2.0, 3.0, 0.0],
    })
    paiements = pd.DataFrame({"order_id": ["o1", "o1", "o2"],
                              "payment_installments": [1, 4, 1]})
    return {"clients": clients, "commandes": commandes, "articles": articles,
            "paiements": paiements}


def test_commandes_livrees_exige_statut_et_date():
    assert list(ex.commandes_livrees(_tables()["commandes"])["order_id"]) == ["o1", "o2"]


def test_clients_perdus():
    t = _tables()
    assert ex.clients_sans_commande_livree(t["clients"], t["commandes"]) == {
        "clients": 3, "gardes": 1, "perdus": 2}  # V (sans date) et W (annulée)


def test_table_commandes_variables():
    t = ex.table_commandes(_tables())
    o1 = t.loc["o1"]
    assert o1["montant_articles"] == 40.0 and o1["frais_port"] == 5.0
    assert o1["nb_articles"] == 2 and o1["nb_vendeurs"] == 2 and o1["mensualites"] == 4
    assert o1["delai_livraison_j"] == 5.5
    assert o1["ecart_prevision_j"] == 1.0  # livrée le 10, promise le 9
    assert t.loc["o2", "ecart_prevision_j"] == -6.0
    assert not any(c.startswith("review_") for c in t.columns)


def test_commandes_par_mois_inclut_les_mois_vides():
    m = ex.commandes_par_mois(_tables()["commandes"])
    assert [str(p) for p in m.index] == ["2017-01", "2017-02", "2017-03"]
    assert m.loc[pd.Period("2017-02", "M"), "toutes"] == 0
    assert m.loc[pd.Period("2017-03", "M")].to_dict() == {"toutes": 3, "livrees": 1}


def test_valeurs_extremes_regle_de_tukey():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 100]})
    r = ex.valeurs_extremes(df, ["x"]).loc["x"]
    assert r["pct_hors_moustaches"] == 20.0
    assert r["positive_ou_nulle"]


def test_repartition_etats_prend_la_derniere_commande():
    t = ex.table_commandes(_tables())
    e = ex.repartition_etats(t)
    assert e["clients"].to_dict() == {"RJ": 1}  # U a commandé depuis SP puis RJ


def test_effet_coupure_par_mois():
    tables = _tables()
    e = ex.effet_coupure(tables["commandes"], ex.table_commandes(tables))
    jan, mar = e.loc[pd.Period("2017-01", "M")], e.loc[pd.Period("2017-03", "M")]
    assert jan["pct_livrees"] == 100.0 and jan["delai_promis_median"] == 4.0
    assert mar["commandes"] == 3 and mar["livrees"] == 1
    assert round(mar["pct_livrees"], 1) == 33.3 and mar["pct_sp"] == 0.0


def test_livraisons_par_semaine():
    s = ex.livraisons_par_semaine(_tables()["commandes"], "2017-01-01")
    assert s.sum() == 2 and len(s) == 2
