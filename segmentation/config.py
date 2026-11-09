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

# ACP (étape 4, voir docs/CHOIX.md) : règles fixées avant le calcul.
ACP = DOSSIER_MODELES / "acp.json"
PART_CUMULEE_MINIMALE = 0.70
SEUIL_NOM_AXE = 0.5
SEUIL_AXE_TEMPS = 0.5
# Étape 5 : partitions (règles fixées et poussées avant tout calcul, voir docs/CHOIX.md).
K_VALEURS = list(range(2, 9))
N_INIT_REFERENCE = 20
N_INIT_BOOTSTRAP = 10
TIRAGES_BOOTSTRAP_K = 50
N_ECHANTILLON_COMMUN = 8000   # silhouettes
N_ECHANTILLON_CAH = 6000      # les 6 000 premiers de l'échantillon commun
MEMOIRE_MIN_CAH_GO = 2.0      # en dessous, le script refuse de démarrer
PART_MIN_SEGMENT = 0.02       # règle de k (admissibilité) : appliquée seulement à l'étape suivante
HDBSCAN_MIN_SAMPLES = 25
AXES_MIXTE = 5
AXES_SENSIBILITE = 4
PARTITIONS = DOSSIER_PROCESSED / "partitions.csv"

# Choix de k (règle appliquée sans modification, critère métier validé : docs/CHOIX.md).
K_RETENU = 5
SEGMENTS = DOSSIER_MODELES / "segments.json"
SEGMENTS_APPRENTISSAGE = DOSSIER_PROCESSED / "segments_apprentissage.csv"
SEGMENTS_NOMS_ACTIONS = {
    0: ("Gros achats en plusieurs fois", "Offres premium et paiement en plusieurs fois"),
    1: ("Petits achats, livraison chère",
        "Livraison gratuite à partir d'un seuil, pour grossir le panier"),
    2: ("Livraison lente ou en retard", "Geste commercial et suivi de la logistique"),
    3: ("Achats de plusieurs articles", "Lots et ventes croisées"),
    4: ("Clients qui recommandent", "Programme de fidélité"),
}
INDICES_PARTITIONS = DOSSIER_RAPPORTS / "indices_partitions.csv"

# Stabilité des axes (description seulement, ne change aucune règle).
TIRAGES_BOOTSTRAP_ACP = 50
# Noms des axes retenus (interprétation validée, voir docs/CHOIX.md ; ne modifie aucun calcul).
NOMS_AXES = {
    "F1": "Valeur de l'achat",
    "F2": "Expérience de livraison",
    "F3": "Taille du panier",
    "F4": "Ancienneté de l'achat (axe du temps)",
    "F5": "Réachat (plutôt qu'achat groupé)",
}

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
