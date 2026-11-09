"""Tests sur les vraies données (ignorés si elles n'ont pas été téléchargées)."""

import json

import pytest

from segmentation import config
from segmentation.donnees import charger_avis, charger_table, charger_tables
from segmentation.telechargement import comparer_au_manifeste, inventaire

pytestmark = pytest.mark.skipif(
    not config.DOSSIER_OLIST.exists(), reason="données absentes : lancer telecharger_donnees.py"
)

COLONNES = {
    "clients": ["customer_id", "customer_unique_id", "customer_zip_code_prefix",
                "customer_city", "customer_state"],
    "commandes": ["order_id", "customer_id", "order_status", "order_purchase_timestamp",
                  "order_approved_at", "order_delivered_carrier_date",
                  "order_delivered_customer_date", "order_estimated_delivery_date"],
    "articles": ["order_id", "order_item_id", "product_id", "seller_id",
                 "shipping_limit_date", "price", "freight_value"],
    "paiements": ["order_id", "payment_sequential", "payment_type",
                  "payment_installments", "payment_value"],
}


def test_fichiers_identiques_au_manifeste():
    manifeste = json.loads(config.MANIFESTE.read_text(encoding="utf-8"))
    assert comparer_au_manifeste(inventaire(config.DOSSIER_OLIST), manifeste) == []
    assert manifeste["octets_total"] == config.OCTETS_ANNONCES


@pytest.mark.parametrize("nom", list(COLONNES))
def test_colonnes_attendues(nom):
    assert list(charger_table(nom).columns) == COLONNES[nom]


def test_les_avis_ne_sortent_jamais_de_charger_tables():
    tables = charger_tables(sauf=("geolocalisation",))
    for nom, df in tables.items():
        assert not any(c.startswith("review_") for c in df.columns), nom
    with pytest.raises(KeyError):
        charger_table("avis")


def test_cles_de_jointure_principales():
    clients, commandes = charger_table("clients"), charger_table("commandes")
    assert commandes["order_id"].is_unique
    assert commandes["customer_id"].is_unique  # un customer_id par commande
    assert commandes["customer_id"].isin(clients["customer_id"]).all()


def test_codes_postaux_gardent_les_zeros():
    zips = charger_table("clients")["customer_zip_code_prefix"]
    assert zips.str.len().eq(5).all()


def test_table_avis_a_la_structure_attendue():
    avis = charger_avis()
    assert set(avis["review_score"].unique()) <= {1, 2, 3, 4, 5}
