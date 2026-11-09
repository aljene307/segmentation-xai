"""Module 3 : modélisation (K-Means, CAH de Ward, classification mixte, HDBSCAN)."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

import commun as C

METHODES = {
    "K-Means (8 variables)": "K-Means sur les 8 variables préparées (référence), 20 initialisations",
    "CAH de Ward (8 variables, 6 000)": "CAH de Ward sur un échantillon de 6 000 clients",
    "Mixte F1–F5": "CAH de Ward sur F1–F5 (6 000 clients), puis consolidation par K-Means",
    "Mixte F1–F4 (sensibilité)": "Même chose avec 4 axes : contrôle de sensibilité",
    "HDBSCAN (F1–F5)": "Densité ; taille minimale 1 297 clients, min_samples 25",
}


def _dendrogramme(d: dict, titre: str) -> alt.Chart:
    lignes = []
    for i, (xs, ys) in enumerate(zip(d["icoord"], d["dcoord"])):
        for j in range(3):  # chaque fusion = 3 segments (montée, barre, descente)
            lignes.append({"fusion": i, "x": xs[j], "y": ys[j], "x2": xs[j + 1], "y2": ys[j + 1]})
    df = pd.DataFrame(lignes)
    return alt.Chart(df).mark_rule(color=C.COULEURS[0], strokeWidth=1.5).encode(
        x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", title="hauteur de fusion (Ward)"),
        x2="x2:Q", y2="y2:Q").properties(
        height=280, title=f"{titre} (cophénétique {C.nombre(d['cophenetique'], 3)})")


def afficher() -> None:
    st.title("3. Modélisation")
    st.markdown("\n".join(f"- **{m}** : {t}" for m, t in METHODES.items()))
    ind = C.indices_partitions()

    k = st.slider("Comparer les méthodes pour k =", 2, 8, C.K_RETENU)
    t = ind[(ind["k"] == k) | (ind["methode"] == "HDBSCAN (F1–F5)")].copy()
    t = t[["methode", "k", "clients", "plus_petit_pct", "bruit_pct", "r2", "silhouette",
           "calinski_harabasz", "davies_bouldin", "cophenetique", "ari_reference"]]
    t.columns = ["méthode", "k", "clients", "plus petit segment (%)", "bruit (%)", "R²",
                 "silhouette", "Calinski-Harabasz", "Davies-Bouldin", "cophénétique",
                 "ARI avec K-Means"]
    st.dataframe(t.round(3), hide_index=True, use_container_width=True)
    st.caption("Indices calculés dans le même espace (les 8 variables préparées). Calinski-Harabasz "
               "augmente avec le nombre de clients : la valeur de la CAH (6 000 clients) n'est pas "
               "comparable aux autres. HDBSCAN trouve lui-même 3 groupes (87,2 %, 8,4 %, 3,0 %) "
               "et 1,4 % de bruit.")

    st.subheader("Dendrogrammes (30 dernières fusions, 6 000 clients)")
    dendros = C.donnee("dendrogrammes.json")
    g, d = st.columns(2)
    g.altair_chart(_dendrogramme(dendros["8 variables"], "CAH de Ward, 8 variables"),
                   use_container_width=True)
    d.altair_chart(_dendrogramme(dendros["F1–F5"], "Classification mixte : CAH sur F1–F5"),
                   use_container_width=True)

    st.subheader("Sensibilité : mixte à 5 axes contre mixte à 4 axes")
    sens = ind[ind["methode"] == "Mixte F1–F4 (sensibilité)"][["k", "ari_mixte5_mixte4"]]
    sens.columns = ["k", "ARI mixte 5 / mixte 4"]
    st.dataframe(sens.round(3).set_index("k").T, use_container_width=True)
    st.caption("Sans F5 (réachat), le segment des clients qui recommandent disparaît : la "
               "classification mixte dépend fortement du choix 4 ou 5 axes. C'est l'une des "
               "raisons, écrites d'avance, de prendre K-Means sur les 8 variables comme référence.")
