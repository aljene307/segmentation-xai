"""Application Streamlit : segmentation explicable des clients Olist.

Lancement local (depuis la racine du projet) :
    .venv\\Scripts\\python -m streamlit run app/app.py

Leçon du projet 1 : tous les imports sont faits ici, AVANT st.navigation.
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))  # paquet `segmentation` (calculs sans scikit-learn)

import streamlit as st  # noqa: E402

from vues import accueil, acp, api, choix_k, donnees, explicabilite, modelisation  # noqa: E402

st.set_page_config(page_title="Segmentation explicable – Olist", layout="wide")

pages = st.navigation([
    st.Page(accueil.afficher, title="Accueil", url_path="accueil", default=True),
    st.Page(donnees.afficher, title="1. Données", url_path="donnees"),
    st.Page(acp.afficher, title="2. Préparation et ACP", url_path="acp"),
    st.Page(modelisation.afficher, title="3. Modélisation", url_path="modelisation"),
    st.Page(choix_k.afficher, title="4. Choix de k", url_path="choix-k"),
    st.Page(explicabilite.afficher, title="5. Explicabilité", url_path="explicabilite"),
    st.Page(api.afficher, title="6. API", url_path="api"),
])
pages.run()
