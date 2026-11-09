"""Page d'accueil : le projet, les données, les 5 segments, l'état de l'API."""

from __future__ import annotations

import pandas as pd
import streamlit as st

import commun as C


def afficher() -> None:
    st.title("Segmentation explicable des clients Olist")
    st.markdown(
        "Application du **projet Challenge 3** (Data Mining, ENSI). Elle construit un profil par "
        "client, le résume par une ACP, compare plusieurs algorithmes de clustering, choisit et "
        "justifie le nombre de segments, les nomme, les explique, propose une action pour chacun "
        "et affecte un nouveau client à son segment grâce à une API.")
    st.info(
        "**Données** : *Brazilian E-Commerce Public Dataset by Olist* (Kaggle), données "
        "**réelles et anonymisées**, licence **CC BY-NC-SA 4.0**. Montants en réals brésiliens "
        "(R$). « Thanks to Olist for releasing this dataset. »")

    st.subheader("Les 5 segments retenus")
    seg = C.modele("segments.json")
    expl = C.modele("explication.json")
    total = seg["clients_apprentissage"]
    st.dataframe(pd.DataFrame([{
        "segment": f"S{s['id']}", "nom": s["nom"], "action proposée": s["action"],
        "part des clients": C.pct(s["clients"] / total),
        "part du chiffre d'affaires": C.pct(expl["part_ca"][str(s["id"])] / 100),
    } for s in seg["segments"]]), hide_index=True, use_container_width=True)
    st.caption(f"Calculé sur les {C.nombre(total, 0)} clients d'apprentissage (80 %), achats "
               "livrés du 2017-01-01 au 2018-06-30.")

    st.subheader("État de l'API")
    st.write(f"Adresse : `{C.adresse_api()}`")
    if st.button("Vérifier l'API"):
        with st.spinner("Interrogation de l'API (jusqu'à une minute si elle dort)…"):
            sante, erreur = C.appeler("GET", "/health")
        if erreur:
            st.error(erreur)
        else:
            m = sante.get("memoire", {})
            st.success(f"API en ligne, version {sante['version']}, k = {sante['k']} ; mémoire "
                       f"{m.get('actuelle_mo', '?')} Mo.")
    st.caption("Sur l'offre gratuite de Render, l'API s'endort après 15 minutes sans requête ; "
               "le premier appel suivant prend environ 30 à 60 secondes.")
