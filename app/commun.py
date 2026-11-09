"""Outils communs de l'application : chemins, données en cache, appels à l'API, mise en forme."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "app" / "donnees"
MODELES = RACINE / "models"
RAPPORTS = RACINE / "reports"
API_PAR_DEFAUT = "https://segmentation-xai-api.onrender.com"
K_RETENU = 5

# Couleurs catégorielles, dans un ordre fixe (segment 0, 1, 2…).
COULEURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6",
            "#e34948"]

VARIABLES = ["recence_j", "frequence", "montant_rs", "part_frais_port", "mensualites_moy",
             "articles_par_commande", "delai_livraison_moy_j", "ecart_prevision_moy_j"]
LIBELLES = {
    "recence_j": "Récence (jours)", "frequence": "Nombre de commandes",
    "montant_rs": "Montant (R$)", "part_frais_port": "Part des frais de port",
    "mensualites_moy": "Mensualités moyennes", "articles_par_commande": "Articles par commande",
    "delai_livraison_moy_j": "Délai de livraison (jours)",
    "ecart_prevision_moy_j": "Écart à la date promise (jours)",
}


def nombre(v: float, d: int = 2) -> str:
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def pct(v: float, d: int = 1) -> str:
    return nombre(100 * v, d) + " %"


def adresse_api() -> str:
    try:
        url = st.secrets.get("API_URL")
    except Exception:  # pas de fichier de secrets en local
        url = None
    return (url or os.environ.get("API_URL") or API_PAR_DEFAUT).rstrip("/")


# --- Données (en cache) -----------------------------------------------------------------

@st.cache_data
def json_local(chemin: str) -> dict | list:
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


def modele(nom: str):
    return json_local(str(MODELES / nom))


def donnee(nom: str):
    return json_local(str(DONNEES / nom))


@st.cache_data
def carte() -> pd.DataFrame:
    return pd.read_csv(DONNEES / "carte.csv")


@st.cache_data
def indices_partitions() -> pd.DataFrame:
    return pd.read_csv(RAPPORTS / "indices_partitions.csv")


def noms_segments() -> dict[int, str]:
    return {s["id"]: s["nom"] for s in modele("segments.json")["segments"]}


def actions_segments() -> dict[int, str]:
    return {s["id"]: s["action"] for s in modele("segments.json")["segments"]}


def libelle_segment(s: int, k: int) -> str:
    return f"S{s} {noms_segments()[s]}" if k == K_RETENU else f"S{s} (exploratoire)"


# --- API -------------------------------------------------------------------------------

def appeler(methode: str, chemin: str, corps=None, delai: int = 90):
    """Appel à l'API ; renvoie (réponse JSON ou None, message d'erreur ou None)."""
    try:
        r = requests.request(methode, adresse_api() + chemin, json=corps, timeout=delai)
    except requests.RequestException as e:
        return None, f"API injoignable ({type(e).__name__}). Elle se réveille peut-être : " \
                     "réessayer dans une minute."
    if r.status_code == 422:
        erreurs = r.json().get("erreurs", [])
        return None, "Données refusées : " + " ; ".join(f"{e['champ']} : {e['message']}"
                                                       for e in erreurs)
    if r.status_code != 200:
        return None, f"Erreur {r.status_code} de l'API."
    return r.json(), None
