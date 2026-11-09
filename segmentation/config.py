"""Paramètres communs à tout le projet (chemins, graine, source des données)."""

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_RAW = RACINE / "data" / "raw"
DOSSIER_OLIST = DOSSIER_RAW / "olist"
FICHIER_ZIP = DOSSIER_RAW / "archive.zip"
MANIFESTE = RACINE / "docs" / "donnees_manifeste.json"
DOSSIER_RAPPORTS = RACINE / "reports"

GRAINE = 42

# Période retenue (dates d'achat), voir docs/CHOIX.md :
# début après la période d'essai de 2016, fin avant la coupure de l'extraction.
DEBUT_ACHATS = "2017-01-01"   # inclus
FIN_ACHATS = "2018-07-01"     # exclu : dernier jour gardé = 2018-06-30
DATE_REFERENCE = "2018-07-01"  # la Récence est comptée à partir de cette date

# Source vérifiée sur la page Kaggle le 2026-11-09 (voir docs/CHOIX.md).
URL_KAGGLE = "https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce"
PAGE_KAGGLE = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
LICENCE = "CC BY-NC-SA 4.0"
OCTETS_ANNONCES = 126_186_995  # champ totalBytes des métadonnées Kaggle

# Limite de sécurité à l'extraction (protection contre une archive piégée).
OCTETS_MAX_EXTRACTION = 500 * 1024 * 1024

# Tables attendues et leurs colonnes.
TABLES = {
    "clients": "olist_customers_dataset.csv",
    "commandes": "olist_orders_dataset.csv",
    "articles": "olist_order_items_dataset.csv",
    "paiements": "olist_order_payments_dataset.csv",
    "produits": "olist_products_dataset.csv",
    "vendeurs": "olist_sellers_dataset.csv",
    "geolocalisation": "olist_geolocation_dataset.csv",
    "traduction_categories": "product_category_name_translation.csv",
}

# La table des avis est tenue à l'écart : elle ne sert qu'à l'évaluation externe.
TABLE_AVIS = "olist_order_reviews_dataset.csv"

COLONNES_DATES = {
    "commandes": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "articles": ["shipping_limit_date"],
}
COLONNES_DATES_AVIS = ["review_creation_date", "review_answer_timestamp"]
