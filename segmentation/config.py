"""Paramètres communs à tout le projet (chemins, graine, source des données)."""

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_RAW = RACINE / "data" / "raw"
DOSSIER_OLIST = DOSSIER_RAW / "olist"
FICHIER_ZIP = DOSSIER_RAW / "archive.zip"
MANIFESTE = RACINE / "docs" / "donnees_manifeste.json"
DOSSIER_RAPPORTS = RACINE / "reports"
DOSSIER_PROCESSED = RACINE / "data" / "processed"
PROFILS_APPRENTISSAGE = DOSSIER_PROCESSED / "profils_apprentissage.csv"
PROFILS_MISE_DE_COTE = DOSSIER_PROCESSED / "profils_mise_de_cote.csv"
EMPREINTE_TIRAGE = RACINE / "docs" / "tirage_empreinte.json"
DOSSIER_MODELES = RACINE / "models"
PREPARATION = DOSSIER_MODELES / "preparation.json"
PREPARES_APPRENTISSAGE = DOSSIER_PROCESSED / "prepares_apprentissage.csv"
PREPARES_MISE_DE_COTE = DOSSIER_PROCESSED / "prepares_mise_de_cote.csv"

# Préparation (étape 3, voir docs/CHOIX.md) : règles fixées avant tout segment.
SEUIL_ASYMETRIE_LOG = 1.0
CENTILES_ECRETAGE = (0.005, 0.995)
# Variables bornées (proportions) : hors de la règle du log par définition.
VARIABLES_BORNEES = ["part_frais_port"]

# Part des clients mise de côté (tirée au hasard par client, graine GRAINE).
PART_MISE_DE_COTE = 0.20

# Variables du profil client utilisées pour le clustering (étape 2, voir docs/CHOIX.md).
VARIABLES_PROFIL = [
    "recence_j",                # jours entre le dernier achat et DATE_REFERENCE
    "frequence",                # nombre de commandes livrées
    "montant_rs",               # somme des prix des articles (R$), sans frais de port
    "part_frais_port",          # frais / (prix + frais), sans unité
    "mensualites_moy",          # nombre moyen de mensualités par commande
    "articles_par_commande",    # nombre moyen d'articles par commande
    "delai_livraison_moy_j",    # moyenne de (livraison - achat), en jours
    "ecart_prevision_moy_j",    # moyenne de (livraison - date promise), en jours ; > 0 = retard
]
# Colonnes gardées seulement pour décrire les segments (jamais dans le clustering).
COLONNES_DESCRIPTION = ["etat", "categorie_principale", "paiement_principal", "premier_achat"]

# Traductions manquantes dans la table officielle (constat du contrôle qualité).
TRADUCTIONS_AJOUTEES = {
    "pc_gamer": "pc_gamer",
    "portateis_cozinha_e_preparadores_de_alimentos": "kitchen_portables_and_food_preparers",
}
CATEGORIE_INCONNUE = "inconnue"

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
