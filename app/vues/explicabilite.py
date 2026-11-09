"""Module 5 : explicabilité (profils, arbre de substitution, explication d'un client par l'API)."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

import commun as C

PARAMETRES = {  # minimum, pas, format du champ de saisie
    "recence_j": (0.0, 1.0, "%.0f"), "frequence": (1, 1, "%d"), "montant_rs": (0.01, 1.0, "%.2f"),
    "part_frais_port": (0.0, 0.01, "%.2f"), "mensualites_moy": (1.0, 1.0, "%.1f"),
    "articles_par_commande": (1.0, 1.0, "%.1f"), "delai_livraison_moy_j": (0.0, 1.0, "%.1f"),
    "ecart_prevision_moy_j": (None, 1.0, "%.1f"),
}


def _profils() -> None:
    expl = C.modele("explication.json")
    noms = C.noms_segments()
    ip = pd.DataFrame(expl["indices_profil"]).T
    ip.index = [f"S{s} {noms[int(s)]}" for s in ip.index]
    df = ip.stack().reset_index()
    df.columns = ["segment", "variable", "indice"]
    df["libellé"] = df["variable"].map(C.LIBELLES)
    ecart = df["variable"] == "ecart_prevision_moy_j"
    df["texte"] = [f"{v:+.1f} j" if e else f"{v:.2f}" for v, e in zip(df["indice"], ecart)]
    df["lecture"] = [0.0 if e else min(max(v - 1, -1), 1)
                     for v, e in zip(df["indice"], ecart)]
    df.loc[ecart, "lecture"] = (df.loc[ecart, "indice"] / 15).clip(-1, 1)
    base = alt.Chart(df).encode(
        x=alt.X("libellé:N", title=None, sort=[C.LIBELLES[v] for v in C.VARIABLES],
                axis=alt.Axis(orient="top", labelAngle=-30, labelLimit=220, labelOverlap=False)),
        y=alt.Y("segment:N", title=None, axis=alt.Axis(labelLimit=260)))
    cases = base.mark_rect().encode(color=alt.Color(
        "lecture:Q", scale=alt.Scale(domain=[-1, 0, 1], range=["#eb6834", "#f0efec", "#2a78d6"],
                        interpolate="rgb"), legend=None), tooltip=["segment", "libellé", "texte"])
    textes = base.mark_text(fontSize=12).encode(text="texte:N")
    st.altair_chart((cases + textes).properties(height=260), use_container_width=True)
    st.caption("Indice de profil = moyenne du segment / moyenne globale (bleu : au-dessus ; "
               "orange : en dessous). Écart à la date promise : différence en jours.")


def _resultat(e: dict) -> None:
    s = e["segment"]
    st.success(e["texte"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Segment", f"S{s['id']}")
    c1.caption(s["nom"])
    c2.metric("Distance au centre", C.nombre(e["distance"], 3))
    c2.caption(f"atypique au-delà de {C.nombre(e['seuil_atypique'], 3)}")
    c3.metric("Rapport des distances", C.nombre(e["rapport_distances"], 2))
    c3.caption(f"à la frontière à partir de {C.nombre(e['seuil_frontiere'], 2)}")
    st.markdown(f"**Action proposée** : {s['action']}. "
                f"**Atypique** : {'oui' if e['atypique'] else 'non'}. "
                f"**À la frontière** : {'oui' if e['frontiere'] else 'non'} (2e segment : "
                f"S{e['deuxieme_segment']['id']} « {e['deuxieme_segment']['nom']} »).")
    if e["ecretees"]:
        st.info("Valeurs hors de la plage apprise, ramenées au seuil : " + " ; ".join(
            f"{C.LIBELLES[x['variable']]} {C.nombre(x['valeur'])} → {C.nombre(x['ramenee_a'])}"
            for x in e["ecretees"]))
    for cle, titre in (("loin_du_client_moyen", "Ce qui explique son segment : ce qui l'éloigne "
                                                "le plus du client moyen"),
                       ("loin_du_centre_du_segment", "Ce qui explique s'il est atypique : ce qui "
                                                     "l'éloigne le plus du centre de son segment")):
        st.markdown(f"**{titre}**")
        st.dataframe(pd.DataFrame([{
            "variable": C.LIBELLES[d["variable"]], "part de l'écart": C.pct(d["part"]),
            "sens": d["sens"], "valeur du client": C.nombre(d["valeur"], 2),
            "moyenne globale": C.nombre(d["moyenne_globale"], 2),
            "médiane du segment": C.nombre(d["mediane_segment"], 2)} for d in e[cle]]),
            hide_index=True, use_container_width=True)
    r = e["regle_arbre"]
    st.markdown(f"**Règle de l'arbre n° {r['numero']}** "
                f"({'en accord' if r['accord'] else 'en désaccord'} avec le segment) : "
                f"{r['phrase']}")
    pts = C.carte()[["F1", "F2", "segment_k5"]].copy()
    pts["segment"] = [C.libelle_segment(x, C.K_RETENU) for x in pts["segment_k5"]]
    domaine = [C.libelle_segment(x, C.K_RETENU) for x in range(C.K_RETENU)]
    nuage = alt.Chart(pts).mark_circle(size=12, opacity=0.35).encode(
        x="F1:Q", y="F2:Q", color=alt.Color("segment:N", scale=alt.Scale(
            domain=domaine, range=C.COULEURS[:C.K_RETENU]), legend=alt.Legend(orient="bottom")))
    client = alt.Chart(pd.DataFrame([{"F1": e["acp"]["F1"], "F2": e["acp"]["F2"]}])).mark_point(
        shape="cross", size=500, color="#0b0b0b", strokeWidth=3).encode(x="F1:Q", y="F2:Q")
    st.altair_chart((nuage + client).properties(height=380, title="Le client (croix) sur la carte"),
                    use_container_width=True)


def afficher() -> None:
    st.title("5. Explicabilité des segments")
    st.subheader("Profils des 5 segments")
    _profils()

    st.subheader("Arbre de décision de substitution (profondeur 4)")
    expl = C.modele("explication.json")
    a = expl["arbre"]
    st.markdown(f"Fidélité : **{C.pct(a['fidelite_80'], 2)}** sur les 80 %, "
                f"**{C.pct(a['fidelite_20'], 2)}** sur les 20 % mis de côté. Profondeur 3 : "
                "83,79 % (sous 90 %) ; profondeur 4 gagne 3,63 points : retenue.")
    with st.expander("Les 13 règles en phrases"):
        for i, p in enumerate(expl["regles"], 1):
            st.markdown(f"{i}. {p}")
    st.caption("Hors de l'arbre : S4 « Clients qui recommandent » est exactement l'ensemble des "
               "clients à au moins 2 commandes (100 %) ; l'arbre ne le retrouve qu'à 71,7 %.")

    st.subheader("Expliquer un client (par l'API)")
    exemples = C.json_local(str(C.RACINE / "data" / "demo" / "exemples.json"))
    choix = st.selectbox("Partir d'un exemple (clients mis de côté, sans identifiant)",
                         range(len(exemples)), format_func=lambda i: exemples[i]["nom"])
    depart = exemples[choix]["client"]
    with st.form("client"):
        colonnes = st.columns(4)
        valeurs = {}
        for i, v in enumerate(C.VARIABLES):
            mini, pas, fmt = PARAMETRES[v]
            valeur = int(depart[v]) if v == "frequence" else float(depart[v])
            valeurs[v] = colonnes[i % 4].number_input(C.LIBELLES[v], value=valeur,
                                                      min_value=mini, step=pas, format=fmt,
                                                      key=f"{v}_{choix}")
        envoyer = st.form_submit_button("Expliquer ce client")
    if envoyer:
        with st.spinner("L'API calcule (jusqu'à une minute si elle dort)…"):
            e, erreur = C.appeler("POST", "/expliquer", valeurs)
        if erreur:
            st.error(erreur)
        else:
            _resultat(e)
