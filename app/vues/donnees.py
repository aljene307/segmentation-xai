"""Module 1 : données et profil client (provenance, qualité, exploration, import de fichier)."""

from __future__ import annotations

import io
import json

import altair as alt
import pandas as pd
import streamlit as st

import commun as C


def _graphique_mois(expl: dict) -> alt.Chart:
    df = pd.DataFrame(expl["commandes_par_mois"])
    debut, fin = expl["periode"]["debut"][:7], expl["periode"]["fin_exclue"][:7]
    df["période retenue"] = [("oui" if debut <= m < fin else "non") for m in df["mois"]]
    return alt.Chart(df).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("mois:N", title="mois d'achat", axis=alt.Axis(labelAngle=-90)),
        y=alt.Y("livrees:Q", title="commandes livrées", axis=alt.Axis(format="d")),
        color=alt.Color("période retenue:N", scale=alt.Scale(domain=["oui", "non"],
                                                             range=[C.COULEURS[0], "#b9b8b2"]),
                        legend=alt.Legend(title="période retenue", orient="top")),
        tooltip=["mois", alt.Tooltip("toutes:Q", title="toutes"),
                 alt.Tooltip("livrees:Q", title="livrées")],
    ).properties(height=260)


def _histogramme(h: dict, titre: str) -> alt.Chart:
    df = pd.DataFrame(h)
    return alt.Chart(df).mark_bar(color=C.COULEURS[0]).encode(
        x=alt.X("debut:Q", title=titre, bin="binned"), x2="fin:Q",
        y=alt.Y("clients:Q", title="clients", axis=alt.Axis(format="d")),
        tooltip=[alt.Tooltip("debut:Q", format=".2f"), alt.Tooltip("fin:Q", format=".2f"),
                 "clients:Q"]).properties(height=220)


def _import_fichier() -> None:
    st.subheader("Importer un fichier de clients")
    st.markdown(
        "Déposer un fichier **CSV** avec une ligne par client et les **8 colonnes** du profil, "
        "en unités d'origine (montants en R$), **1 000 clients au plus**. Chaque ligne est "
        "affectée à un segment par l'API ; une ligne invalide n'empêche pas les autres.")
    modele_csv = pd.DataFrame([e["client"] for e in C.json_local(
        str(C.RACINE / "data" / "demo" / "exemples.json"))])[C.VARIABLES]
    st.download_button("Télécharger un modèle de fichier (10 exemples)",
                       modele_csv.to_csv(index=False).encode("utf-8"), "modele_clients.csv",
                       "text/csv")
    fichier = st.file_uploader("Fichier CSV", type=["csv"])
    if fichier is None:
        return
    try:
        df = pd.read_csv(fichier)
    except Exception as e:  # fichier illisible
        st.error(f"Fichier illisible : {e}")
        return
    manquantes = [c for c in C.VARIABLES if c not in df.columns]
    if manquantes:
        st.error("Colonnes manquantes : " + ", ".join(manquantes))
        return
    if len(df) > 1000:
        st.error(f"{len(df)} lignes : 1 000 au plus.")
        return
    # Conversion JSON par pandas : types numpy → nombres JSON, cases vides → null.
    lignes = json.loads(df[C.VARIABLES].to_json(orient="records"))
    with st.spinner("Affectation par l'API…"):
        rep, erreur = C.appeler("POST", "/affecter/lot", {"clients": lignes}, delai=120)
    if erreur:
        st.error(erreur)
        return
    sortie = df[C.VARIABLES].copy()
    sortie["segment"] = [f"S{r['segment']['id']} {r['segment']['nom']}" if "segment" in r
                         else "" for r in rep["resultats"]]
    sortie["action"] = [r["segment"]["action"] if "segment" in r else ""
                        for r in rep["resultats"]]
    sortie["erreurs"] = [" ; ".join(f"{e['champ']} : {e['message']}" for e in r.get("erreurs", []))
                         for r in rep["resultats"]]
    st.success(f"{rep['valides']} ligne(s) affectée(s), {rep['invalides']} ligne(s) refusée(s).")
    st.dataframe(sortie, use_container_width=True)
    tampon = io.StringIO()
    sortie.to_csv(tampon, index=False)
    st.download_button("Télécharger le résultat (CSV)", tampon.getvalue().encode("utf-8"),
                       "clients_segments.csv", "text/csv")


def afficher() -> None:
    st.title("1. Données et profil client")
    expl = C.donnee("exploration.json")
    ch = expl["chaine_clients"]
    st.markdown(
        "Le jeu Olist est **téléchargé automatiquement** depuis Kaggle par "
        "`scripts/telecharger_donnees.py` (126 186 995 octets, 9 fichiers, empreintes SHA-256 "
        "vérifiées). Un **profil par client** (`customer_unique_id`) est construit à partir des "
        "commandes livrées, avec 8 variables. **La note d'avis n'entre jamais dans le "
        "clustering** : elle sert seulement à évaluer les segments.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("vrais clients", C.nombre(ch["tous"], 0))
    c2.metric("avec une commande livrée", C.nombre(ch["au_moins_une_livree"], 0))
    c3.metric("dans la période", C.nombre(ch["periode"], 0))
    c4.metric("apprentissage (80 %)", C.nombre(ch["apprentissage"], 0))

    st.subheader("Commandes par mois")
    st.altair_chart(_graphique_mois(expl), use_container_width=True)
    st.caption("Période retenue : achats du 2017-01-01 au 2018-06-30. Fin 2016 : période d'essai ; "
               "après juin 2018 : coupure de l'extraction (livraisons lentes absentes).")

    st.subheader("Distributions et valeurs extrêmes")
    var = st.selectbox("Variable", C.VARIABLES, format_func=C.LIBELLES.get, index=2)
    h = expl["histogrammes"][var]
    prep = C.modele("preparation.json")["parametres"][var]
    g, d = st.columns(2)
    g.altair_chart(_histogramme(h["brut"], C.LIBELLES[var] + " (0,5e – 99,5e centile)"),
                   use_container_width=True)
    d.altair_chart(_histogramme(h["prepare"], "après préparation (z)"), use_container_width=True)
    st.caption(f"Log : {'oui' if prep['log'] else 'non'} ({prep['raison']}). Asymétrie brute "
               f"{C.nombre(prep['asymetrie_brute'])}. Écrêtage aux 0,5e et 99,5e centiles, appris "
               "sur les 80 %.")

    st.subheader("Corrélations (Spearman) entre les 8 variables")
    cor = pd.DataFrame(expl["correlations_spearman"]).stack().reset_index()
    cor.columns = ["variable 1", "variable 2", "corrélation"]
    cor["variable 1"] = cor["variable 1"].map(C.LIBELLES)
    cor["variable 2"] = cor["variable 2"].map(C.LIBELLES)
    ordre = [C.LIBELLES[v] for v in C.VARIABLES]
    st.altair_chart(alt.Chart(cor).mark_rect().encode(
        x=alt.X("variable 1:N", sort=ordre, title=None,
                axis=alt.Axis(labelAngle=-30, labelLimit=220, labelOverlap=False)),
        y=alt.Y("variable 2:N", sort=ordre, title=None, axis=alt.Axis(labelLimit=220)),
        color=alt.Color("corrélation:Q", scale=alt.Scale(domain=[-1, 0, 1],
                                                         range=["#eb6834", "#f0efec", "#2a78d6"],
                                                         interpolate="rgb")),
        tooltip=["variable 1", "variable 2", alt.Tooltip("corrélation:Q", format=".2f")],
    ).properties(height=330), use_container_width=True)

    st.subheader("Clients par État (description seulement, hors clustering)")
    etats = pd.Series(expl["etats"]).rename_axis("État").reset_index(name="clients")
    st.altair_chart(alt.Chart(etats.head(12)).mark_bar(color=C.COULEURS[0]).encode(
        x=alt.X("clients:Q", axis=alt.Axis(format="d")), y=alt.Y("État:N", sort="-x"), tooltip=["État", "clients"]),
        use_container_width=True)

    st.divider()
    _import_fichier()
