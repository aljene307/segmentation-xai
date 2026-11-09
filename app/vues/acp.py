"""Module 2 : préparation des variables et ACP normée."""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import commun as C
from segmentation import acp as A
from segmentation import preparation as prepa

NOMS_AXES = {"F1": "Valeur de l'achat", "F2": "Expérience de livraison", "F3": "Taille du panier",
             "F4": "Ancienneté de l'achat (axe du temps)",
             "F5": "Réachat (plutôt qu'achat groupé)"}


def _cercle(corr: pd.DataFrame, a: str, b: str, parts: dict) -> alt.LayerChart:
    t = np.linspace(0, 2 * np.pi, 200)
    rond = alt.Chart(pd.DataFrame({"x": np.cos(t), "y": np.sin(t), "o": range(200)})).mark_line(
        color="#52514e", strokeWidth=1).encode(x="x:Q", y="y:Q", order="o:Q")
    d = pd.DataFrame({"variable": [C.LIBELLES[v] for v in corr.index], "x": corr[a].to_numpy(),
                      "y": corr[b].to_numpy(), "x0": 0.0, "y0": 0.0})
    d["qualité"] = d["x"] ** 2 + d["y"] ** 2
    d["représentation"] = np.where(d["qualité"] >= 0.25, "bonne (cos² ≥ 0,25)", "faible")
    echelle = alt.Scale(domain=[-1.15, 1.15])
    fleches = alt.Chart(d).mark_rule(strokeWidth=2).encode(
        x=alt.X("x0:Q", scale=echelle, title=f"{a} ({C.nombre(parts[a], 1)} %)"),
        y=alt.Y("y0:Q", scale=echelle, title=f"{b} ({C.nombre(parts[b], 1)} %)"),
        x2="x:Q", y2="y:Q",
        color=alt.Color("représentation:N", scale=alt.Scale(
            domain=["bonne (cos² ≥ 0,25)", "faible"], range=[C.COULEURS[0], "#b9b8b2"]),
            legend=alt.Legend(orient="bottom")),
        tooltip=["variable", alt.Tooltip("x:Q", format=".2f", title=a),
                 alt.Tooltip("y:Q", format=".2f", title=b)])
    points = alt.Chart(d).mark_circle(size=60).encode(x="x:Q", y="y:Q",
                                                       color=alt.Color("représentation:N"))
    textes = alt.Chart(d).mark_text(dx=8, dy=-8, fontSize=11, align="left").encode(
        x="x:Q", y="y:Q", text="variable:N")
    return (rond + fleches + points + textes).properties(width=430, height=430)


def afficher() -> None:
    st.title("2. Préparation et ACP normée")

    st.subheader("Préparation (apprise sur les 80 %, réappliquée telle quelle)")
    prep = C.modele("preparation.json")
    unites = prepa.seuils_en_unites(prep)
    st.dataframe(pd.DataFrame([{
        "variable": C.LIBELLES[v], "log(1 + x)": "oui" if p["log"] else "non",
        "raison": p["raison"], "asymétrie brute": round(p["asymetrie_brute"], 2),
        "seuil bas": round(unites[v][0], 2), "seuil haut": round(unites[v][1], 2),
    } for v, p in prep["parametres"].items()]), hide_index=True, use_container_width=True)
    st.caption("Ordre : log → écrêtage aux 0,5e et 99,5e centiles → standardisation. Aucune "
               "pondération. Règles fixées avant tout segment.")

    acp = C.modele("acp.json")
    vp = np.asarray(acp["valeurs_propres"])
    parts = {f"F{i + 1}": 100 * x / vp.sum() for i, x in enumerate(vp)}
    k = acp["decision"]["retenus"]
    st.subheader("Valeurs propres et nombre d'axes")
    df = pd.DataFrame({"axe": list(parts), "valeur propre": vp,
                       "part cumulée (%)": 100 * np.cumsum(vp) / vp.sum(),
                       "retenu": ["oui" if i < k else "non" for i in range(len(vp))]})
    g, d = st.columns(2)
    barres = alt.Chart(df).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("axe:N", sort=None), y="valeur propre:Q",
        color=alt.Color("retenu:N", scale=alt.Scale(domain=["oui", "non"],
                                                    range=[C.COULEURS[0], "#b9b8b2"])),
        tooltip=["axe", alt.Tooltip("valeur propre:Q", format=".3f")])
    kaiser = alt.Chart(pd.DataFrame({"y": [1]})).mark_rule(color=C.COULEURS[1],
                                                           strokeDash=[4, 4]).encode(y="y:Q")
    g.altair_chart((barres + kaiser).properties(height=260, title="Valeurs propres (Kaiser = 1)"),
                   use_container_width=True)
    ligne = alt.Chart(df).mark_line(point=True, color=C.COULEURS[0]).encode(
        x=alt.X("axe:N", sort=None), y=alt.Y("part cumulée (%):Q", scale=alt.Scale(domain=[0, 100])),
        tooltip=["axe", alt.Tooltip("part cumulée (%):Q", format=".2f")])
    seuil = alt.Chart(pd.DataFrame({"y": [70]})).mark_rule(color=C.COULEURS[1],
                                                           strokeDash=[4, 4]).encode(y="y:Q")
    d.altair_chart((ligne + seuil).properties(height=260, title="Part cumulée (seuil 70 %)"),
                   use_container_width=True)
    dec = acp["decision"]
    st.markdown(f"**Règle fixée avant le calcul** : max(Kaiser, part cumulée ≥ 70 %). Kaiser : "
                f"{dec['kaiser']} axes ; part cumulée : {dec['part_cumulee']} axes (F4 atteint "
                f"69,97 %, juste sous le seuil) ; coude : indicatif. **{k} axes retenus** "
                f"({C.nombre(df['part cumulée (%)'].iloc[k - 1], 1)} % de l'information).")

    st.subheader("Cercle des corrélations")
    axes = [f"F{i + 1}" for i in range(k)]
    c1, c2 = st.columns(2)
    a = c1.selectbox("Axe horizontal", axes, index=0)
    b = c2.selectbox("Axe vertical", [x for x in axes if x != a], index=0)
    corr = A.correlations(acp)
    st.altair_chart(_cercle(corr, a, b, parts), use_container_width=False)

    st.subheader("Noms des axes et qualité de représentation (cos²)")
    cos2 = (corr[axes] ** 2)
    tableau = cos2.copy()
    tableau["somme (qualité)"] = cos2.sum(axis=1)
    tableau.index = [C.LIBELLES[v] for v in tableau.index]
    st.dataframe(tableau.round(2), use_container_width=True)
    st.markdown("\n".join(f"- **{ax}** ({C.nombre(parts[ax], 1)} %) : {NOMS_AXES[ax]}"
                          for ax in axes))
    st.info("**Axe du temps** : F4 est presque la Récence seule (corrélation 0,90 ; avec la date "
            "d'achat −0,86). Un segment séparé surtout par F4 signifie « une autre période "
            "d'achat », pas un autre comportement. **Stabilité** (50 tirages bootstrap) : F1 et F2 "
            "parfaitement stables ; F3 à F5 tournent un peu entre eux, mais le sous-espace des "
            "5 axes est très stable (environ 3° au pire). Les mensualités sont mal représentées "
            "sur les 5 axes (qualité 0,44).")
