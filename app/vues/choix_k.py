"""Module 4 : choix du nombre de segments et validation (curseur k mis à jour en direct)."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

import commun as C
from segmentation import regle_k as R

INDICES = [("r2", "R²"), ("silhouette", "Silhouette ↑"), ("calinski_harabasz", "Calinski-Harabasz ↑"),
           ("davies_bouldin", "Davies-Bouldin ↓"), ("ari_boot_moyen", "ARI bootstrap moyen ↑")]


def _courbe(km: pd.DataFrame, col: str, titre: str, k: int) -> alt.LayerChart:
    """Un seul jeu de données : la courbe, et le k choisi repéré par la colonne « choisi »
    (deux jeux séparés ne se redessinaient pas toujours après un changement du curseur)."""
    d = km[["k", col]].copy()
    d["choisi"] = d["k"] == k
    base = alt.Chart(d).encode(x=alt.X("k:O", title="k"))
    ligne = base.mark_line(point=True, color=C.COULEURS[0]).encode(
        y=alt.Y(f"{col}:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(format="~g")),
        tooltip=["k", alt.Tooltip(f"{col}:Q", format=".4f")])
    repere = base.mark_rule(color=C.COULEURS[1], strokeWidth=2).transform_filter(
        alt.datum.choisi)
    return (ligne + repere).properties(height=170, title=titre)


def _carte(k: int) -> alt.LayerChart:
    pts = C.carte()[["F1", "F2", f"segment_k{k}"]].rename(columns={f"segment_k{k}": "s"})
    pts["segment"] = [C.libelle_segment(s, k) for s in pts["s"]]
    domaine = [C.libelle_segment(s, k) for s in range(k)]
    couleur = alt.Color("segment:N", scale=alt.Scale(domain=domaine, range=C.COULEURS[:k]),
                        legend=alt.Legend(orient="bottom", columns=2))
    nuage = alt.Chart(pts).mark_circle(size=14, opacity=0.55).encode(
        x=alt.X("F1:Q", title="F1 Valeur de l'achat"),
        y=alt.Y("F2:Q", title="F2 Expérience de livraison"), color=couleur,
        tooltip=["segment"])
    cen = pd.DataFrame([{"F1": p["centre_F1"], "F2": p["centre_F2"],
                         "segment": C.libelle_segment(p["segment"], k)}
                        for p in C.donnee("profils_k.json")[str(k)]])
    centres = alt.Chart(cen).mark_point(shape="diamond", size=260, filled=True, stroke="white",
                                        strokeWidth=2).encode(x="F1:Q", y="F2:Q", color=couleur,
                                                              tooltip=["segment"])
    return (nuage + centres).properties(height=480)


def afficher() -> None:
    st.title("4. Choix du nombre de segments et validation")
    k = st.slider("Nombre de segments k", 2, 8, C.K_RETENU,
                  help="Tout ce qui suit se met à jour : indices, stabilité, profils, carte.")
    if k == C.K_RETENU:
        st.success("k = 5 : **retenu par la règle** écrite avant tout calcul ; segments nommés.")
    else:
        st.warning(f"k = {k} : segments **exploratoires**, sans nom ni action (k = 5 est retenu).")

    ind = C.indices_partitions()
    km = ind[ind["methode"] == "K-Means (8 variables)"].copy()
    st.subheader("Indices internes et stabilité (K-Means, 8 variables)")
    colonnes = st.columns(5)
    for c, (col, titre) in zip(colonnes, INDICES):
        c.altair_chart(_courbe(km, col, titre, k), use_container_width=True)
    ligne = km[km["k"] == k].iloc[0]
    jac = [float(x) for x in str(ligne["jaccard_segments"]).split(" ; ")]
    sil = C.donnee("silhouette_k.json")[str(k)]
    profils = C.donnee("profils_k.json")[str(k)]

    st.subheader(f"Segments pour k = {k}")
    t = pd.DataFrame([{
        "segment": C.libelle_segment(p["segment"], k),
        "clients": C.nombre(p["clients"], 0), "part": C.pct(p["part_clients"]),
        "part du CA": C.pct(p["part_ca"]), "Jaccard bootstrap": C.nombre(jac[p["segment"]], 2),
        "silhouette moyenne": C.nombre(sil["segments"][p["segment"]]["moyenne"], 3),
        "silhouette négative": C.pct(sil["segments"][p["segment"]]["part_negative"]),
    } for p in profils])
    st.dataframe(t, hide_index=True, use_container_width=True)
    st.caption(f"Silhouette moyenne {C.nombre(sil['moyenne'], 4)} ; {C.pct(sil['part_negative'])} "
               f"de clients à silhouette négative (échantillon commun de 8 000 clients). ARI "
               f"bootstrap moyen {C.nombre(ligne['ari_boot_moyen'], 3)} (minimum "
               f"{C.nombre(ligne['ari_boot_min'], 3)}).")

    st.subheader("Carte de l'ACP (3 000 clients, F1 – F2)")
    st.altair_chart(_carte(k), use_container_width=True)

    st.subheader("Profils : médianes (unités d'origine)")
    med = pd.DataFrame([{"segment": C.libelle_segment(p["segment"], k),
                         **{C.LIBELLES[v]: C.nombre(p["medianes"][v], 2) for v in C.VARIABLES}}
                        for p in profils])
    st.dataframe(med, hide_index=True, use_container_width=True)

    st.divider()
    st.subheader("La règle de choix de k (écrite et poussée avant tout calcul)")
    tab = km.set_index("k")
    choix = R.choisir_k(tab)
    r = choix["rangs"].join(choix["admissibilite"]["admissible"])
    r.columns = ["rang silhouette", "rang Calinski-Harabasz", "rang Davies-Bouldin", "somme",
                 "admissible"]
    st.dataframe(r, use_container_width=True)
    st.markdown(f"Admissible : plus petit segment ≥ 2 %, ARI bootstrap moyen ≥ 0,80, Jaccard de "
                f"chaque segment ≥ 0,60. Parmi les admissibles, la plus petite somme des rangs "
                f"gagne : **k = {choix['k']}**. Critère métier validé : chaque segment reçoit une "
                "action différente.")

    st.subheader("Évaluation externe (note d'avis) et évaluation finale sur les 20 %")
    st.warning("Le segment S2 « Livraison lente ou en retard » est lié à la note **par "
               "construction** (un retard entraîne souvent une mauvaise note). Les indices "
               "externes (ARI, NMI) sont faibles par nature avec une étiquette à deux classes.")
    ev = C.json_local(str(C.RAPPORTS / "evaluation_finale.json"))
    noms = C.noms_segments()
    st.dataframe(pd.DataFrame([{
        "segment": f"S{s} {noms[s]}",
        "satisfaits (80 %)": C.pct(ev["mesures_80"]["satisfaits_par_segment"][s]),
        "satisfaits (20 %, jamais vus)": C.pct(ev["mesures_20"]["satisfaits_par_segment"][s]),
    } for s in range(C.K_RETENU)]), hide_index=True, use_container_width=True)
    st.dataframe(pd.DataFrame([{
        "n°": v["code"], "mesure": v["mesure"], "attente": v["attente"],
        "atteinte": "oui" if v["atteinte"] else "NON", "statut": v["statut"]}
        for v in ev["verdicts"]]), hide_index=True, use_container_width=True)
    st.caption("Évaluation finale ouverte une seule fois, attentes écrites avant l'ouverture : "
               f"{sum(v['atteinte'] for v in ev['verdicts'])} attentes atteintes sur "
               f"{len(ev['verdicts'])}. Limite : les 20 % viennent de la même période ; la "
               "segmentation devrait être refaite régulièrement.")
