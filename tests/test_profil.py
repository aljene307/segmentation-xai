"""Tests du profil client sur un petit jeu construit à la main (valeurs calculées à la main)."""

import pandas as pd
import pytest

from segmentation import config
from segmentation.profil import construire_profil

T = pd.Timestamp


def _tables():
    clients = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3", "c4", "c5"],
        "customer_unique_id": ["A", "A", "B", "C", "D"],
        "customer_state": ["SP", "RJ", "MG", "SP", "BA"],
    })
    commandes = pd.DataFrame({
        "order_id": ["o1", "o2", "o3", "o4", "o5"],
        "customer_id": ["c1", "c2", "c3", "c4", "c5"],
        "order_status": ["delivered", "delivered", "delivered", "canceled", "delivered"],
        # o5 est achetée hors période (2016) : D ne doit pas apparaître.
        "order_purchase_timestamp": [T("2018-06-01 10:00"), T("2018-06-20 18:00"),
                                     T("2017-03-01"), T("2018-01-01"), T("2016-10-01")],
        "order_delivered_customer_date": [T("2018-06-05 10:00"), T("2018-06-30 18:00"),
                                          T("2017-03-11"), pd.NaT, T("2016-10-10")],
        "order_estimated_delivery_date": [T("2018-06-10"), T("2018-06-25"), T("2017-03-20"),
                                          T("2018-01-20"), T("2016-10-20")],
    })
    articles = pd.DataFrame({
        "order_id": ["o1", "o1", "o2", "o3", "o4", "o5"],
        "order_item_id": [1, 2, 1, 1, 1, 1],
        "product_id": ["p1", "p2", "p3", "p4", "p1", "p1"],
        "seller_id": ["s1"] * 6,
        "price": [60.0, 20.0, 100.0, 50.0, 10.0, 10.0],
        "freight_value": [10.0, 10.0, 0.0, 50.0, 1.0, 1.0],
    })
    paiements = pd.DataFrame({
        "order_id": ["o1", "o2", "o2", "o3", "o5"],
        "payment_type": ["credit_card", "boleto", "voucher", "credit_card", "boleto"],
        "payment_installments": [3, 1, 1, 0, 1],
        "payment_value": [100.0, 70.0, 30.0, 100.0, 11.0],
    })
    produits = pd.DataFrame({
        "product_id": ["p1", "p2", "p3", "p4"],
        "product_category_name": ["cama_mesa_banho", "pc_gamer", "cama_mesa_banho", None],
    })
    traduction = pd.DataFrame({"product_category_name": ["cama_mesa_banho"],
                               "product_category_name_english": ["bed_bath_table"]})
    return {"clients": clients, "commandes": commandes, "articles": articles,
            "paiements": paiements, "produits": produits, "traduction_categories": traduction}


@pytest.fixture(scope="module")
def profil():
    return construire_profil(_tables(), "2017-01-01", "2018-07-01", "2018-07-01")


def test_clients_retenus(profil):
    # A (2 commandes livrées), B ; C n'a qu'une commande annulée, D est hors période.
    assert list(profil.index) == ["A", "B"]


def test_colonnes_et_absence_d_avis(profil):
    assert list(profil.columns) == config.VARIABLES_PROFIL + config.COLONNES_DESCRIPTION
    assert not any("review" in c for c in profil.columns)


def test_rfm(profil):
    a, b = profil.loc["A"], profil.loc["B"]
    assert a["recence_j"] == 11      # 2018-07-01 - 2018-06-20
    assert b["recence_j"] == 487     # 2018-07-01 - 2017-03-01
    assert a["frequence"] == 2 and b["frequence"] == 1
    assert a["montant_rs"] == 180.0  # 60 + 20 + 100, sans frais de port


def test_part_frais_port(profil):
    assert profil.loc["A", "part_frais_port"] == pytest.approx(20 / 200)
    assert profil.loc["B", "part_frais_port"] == pytest.approx(0.5)


def test_mensualites_zero_compte_comme_un(profil):
    assert profil.loc["A", "mensualites_moy"] == 2.0  # (3 + 1) / 2
    assert profil.loc["B", "mensualites_moy"] == 1.0  # 0 corrigé en 1


def test_articles_et_delais(profil):
    a = profil.loc["A"]
    assert a["articles_par_commande"] == 1.5           # (2 + 1) / 2
    assert a["delai_livraison_moy_j"] == pytest.approx(7.0)   # (4 + 10) / 2
    assert a["ecart_prevision_moy_j"] == pytest.approx(0.0)   # (-5 + 5) / 2
    assert profil.loc["B", "ecart_prevision_moy_j"] == -9.0


def test_colonnes_de_description(profil):
    a, b = profil.loc["A"], profil.loc["B"]
    assert a["etat"] == "RJ"                              # État de la dernière commande
    assert a["categorie_principale"] == "bed_bath_table"  # 160 R$ contre 20 R$ (pc_gamer)
    assert a["paiement_principal"] == "credit_card"       # 100 R$ contre 70 et 30
    assert b["categorie_principale"] == config.CATEGORIE_INCONNUE
    assert str(a["premier_achat"]) == "2018-06-01"


def test_traduction_ajoutee():
    t = _tables()
    t["articles"].loc[t["articles"]["order_id"] == "o1", "price"] = [1.0, 500.0]
    p = construire_profil(t, "2017-01-01", "2018-07-01", "2018-07-01")
    assert p.loc["A", "categorie_principale"] == "pc_gamer"
