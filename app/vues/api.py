"""Module 6 : l'API FastAPI."""

from __future__ import annotations

import json

import streamlit as st

import commun as C

EXEMPLE = {"recence_j": 120, "frequence": 1, "montant_rs": 89.9, "part_frais_port": 0.18,
           "mensualites_moy": 2, "articles_par_commande": 1, "delai_livraison_moy_j": 9.5,
           "ecart_prevision_moy_j": -12}


def afficher() -> None:
    st.title("6. API")
    url = C.adresse_api()
    st.markdown(f"Adresse : `{url}` — documentation interactive : [{url}/docs]({url}/docs)")
    st.markdown("""
| méthode | adresse | rôle |
|---|---|---|
| GET | `/health` | état, empreintes des modèles, mémoire du processus |
| GET | `/segments`, `/segments/{id}` | description des segments (nom, action, profils) |
| GET | `/regles` | les 13 règles de l'arbre en phrases et leur fidélité |
| POST | `/affecter` | segment d'un client (8 variables en unités d'origine) |
| POST | `/affecter/lot` | jusqu'à 1 000 clients ; erreurs ligne par ligne |
| POST | `/expliquer` | segment, distances, atypique, frontière, variables, règle, carte |
| GET | `/exemples` | 10 clients de démonstration, sans identifiant |
""")
    st.markdown("La chaîne est **figée** : préparation, centres, explication et arbre sont lus dans "
                "des fichiers JSON vérifiés par leurs empreintes ; l'API n'utilise ni "
                "scikit-learn ni scipy. Les erreurs sont renvoyées en français.")
    st.subheader("Exemple d'appel (Python)")
    st.code(f"import requests\nr = requests.post(\"{url}/affecter\", json={json.dumps(EXEMPLE)})"
            "\nprint(r.json())", language="python")
    if st.button("Essayer cet appel"):
        with st.spinner("Appel en cours…"):
            rep, erreur = C.appeler("POST", "/affecter", EXEMPLE)
        st.error(erreur) if erreur else st.json(rep)
