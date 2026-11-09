"""Précalcule les petits fichiers de l'application Streamlit (app/donnees/), SANS identifiant.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\preparer_app.py

Sorties (versionnées, licence CC BY-NC-SA 4.0 : app/donnees/LICENCE.md) :
    carte.csv           3 000 clients d'apprentissage : F1, F2, segment pour k = 2 à 8
    profils_k.json      pour chaque k : effectif, part du CA, médianes, indices de profil, centres
    silhouette_k.json   silhouette détaillée (moyenne par segment, part négative), k = 2 à 8
    dendrogrammes.json  30 dernières fusions des deux CAH (8 variables ; F1–F5)
    exploration.json    agrégats : commandes par mois, histogrammes, corrélations, États
Pour k = 5, les segments sont les segments officiels ; pour les autres k, la partition K-Means
de l'étape 5 (exploratoire). Aucun avis n'est utilisé ici.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram
from sklearn.metrics import silhouette_samples

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import acp as A  # noqa: E402
from segmentation import config  # noqa: E402
from segmentation import explication as X  # noqa: E402
from segmentation import exploration as ex  # noqa: E402
from segmentation import partitions as P  # noqa: E402
from segmentation import preparation as prepa  # noqa: E402
from segmentation import segments as S  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402
from segmentation.donnees import charger_tables  # noqa: E402
from segmentation.telechargement import ecrire_json  # noqa: E402

DOSSIER = config.RACINE / "app" / "donnees"
N_CARTE = 3000


def histogramme(x: pd.Series, bornes=None, n=40) -> dict:
    compte, aretes = np.histogram(x, bins=n, range=bornes)
    return {"debut": aretes[:-1].round(4).tolist(), "fin": aretes[1:].round(4).tolist(),
            "clients": compte.tolist()}


def main() -> int:
    proteger_sorties()
    DOSSIER.mkdir(parents=True, exist_ok=True)
    v = config.VARIABLES_PROFIL
    z = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    prof = pd.read_csv(config.PROFILS_APPRENTISSAGE, index_col="customer_unique_id").loc[z.index]
    lab = pd.read_csv(config.PARTITIONS, index_col="customer_unique_id").loc[z.index]
    acp = A.charger(config.ACP)
    f = A.projeter(z, acp, 5)
    officiel = S.segments_apprentissage().loc[z.index]
    etiquettes = {k: (officiel if k == config.K_RETENU else lab[f"kmeans_k{k}"])
                  for k in config.K_VALEURS}

    # 1. Carte : 3 000 clients (les premiers de l'échantillon commun), sans identifiant.
    ordre = P.ordre_echantillon(z.index, config.GRAINE)
    carte_ids = ordre[:N_CARTE]
    carte = pd.DataFrame({"F1": f.loc[carte_ids, "F1"].round(4).to_numpy(),
                          "F2": f.loc[carte_ids, "F2"].round(4).to_numpy()})
    for k, e in etiquettes.items():
        carte[f"segment_k{k}"] = e.loc[carte_ids].to_numpy()
    carte.to_csv(DOSSIER / "carte.csv", index=False, encoding="utf-8", lineterminator="\n")

    # 2. Profils par k.
    profils = {}
    for k, e in etiquettes.items():
        ip = X.indices_profil(prof, e, v)
        ca = X.part_ca(prof, e)
        med = prof[v].groupby(e).median()
        cen = f[["F1", "F2"]].groupby(e).mean()
        profils[str(k)] = [{
            "segment": int(s), "clients": int((e == s).sum()),
            "part_clients": float((e == s).mean()), "part_ca": float(ca[s] / 100),
            "medianes": {c: float(med.loc[s, c]) for c in v},
            "indices_profil": {c: float(ip.loc[s, c]) for c in v},
            "centre_F1": float(cen.loc[s, "F1"]), "centre_F2": float(cen.loc[s, "F2"]),
        } for s in range(k)]
    ecrire_json(DOSSIER / "profils_k.json", profils)

    # 3. Silhouette détaillée sur l'échantillon commun (8 000 clients).
    commun = ordre[:config.N_ECHANTILLON_COMMUN]
    xc = z.loc[commun, v].to_numpy(dtype=float)
    sil = {}
    for k, e in etiquettes.items():
        ec = e.loc[commun].to_numpy()
        s = silhouette_samples(xc, ec)
        sil[str(k)] = {"moyenne": float(s.mean()), "part_negative": float((s < 0).mean()),
                       "segments": [{"segment": int(g), "clients_echantillon": int((ec == g).sum()),
                                     "moyenne": float(s[ec == g].mean()),
                                     "part_negative": float((s[ec == g] < 0).mean())}
                                    for g in range(k)]}
    ecrire_json(DOSSIER / "silhouette_k.json", sil)

    # 4. Dendrogrammes (30 dernières fusions, échantillon de la CAH : 6 000 clients).
    cah = ordre[:config.N_ECHANTILLON_CAH]
    dendros = {}
    for nom, donnees in (("8 variables", z.loc[cah, v]), ("F1–F5", f.loc[cah])):
        arbre, coph = P.cah_ward(donnees.to_numpy(dtype=float))
        d = dendrogram(arbre, truncate_mode="lastp", p=30, no_plot=True)
        dendros[nom] = {"cophenetique": coph, "icoord": d["icoord"], "dcoord": d["dcoord"],
                        "feuilles": d["ivl"]}
    ecrire_json(DOSSIER / "dendrogrammes.json", dendros)

    # 5. Exploration (agrégats seulement).
    tables = charger_tables(sauf=("geolocalisation",))
    perte = ex.clients_sans_commande_livree(tables["clients"], tables["commandes"])
    mois = ex.commandes_par_mois(tables["commandes"])
    prep = prepa.charger(config.PREPARATION)
    zt = prepa.appliquer(prof, prep)
    histo = {}
    for c in v:
        bas, haut = prof[c].quantile([0.005, 0.995])
        histo[c] = {"brut": histogramme(prof[c], (float(bas), float(haut))),
                    "brut_bornes_affichees": [float(bas), float(haut)],
                    "prepare": histogramme(zt[c])}
    exploration = {
        "chaine_clients": {"tous": perte["clients"], "au_moins_une_livree": perte["gardes"],
                           "periode": int(len(pd.read_csv(config.PROFILS_APPRENTISSAGE,
                                                          usecols=["customer_unique_id"]))
                                          + len(pd.read_csv(config.PROFILS_MISE_DE_COTE,
                                                            usecols=["customer_unique_id"]))),
                           "apprentissage": int(len(z))},
        "periode": {"debut": config.DEBUT_ACHATS, "fin_exclue": config.FIN_ACHATS,
                    "date_reference": config.DATE_REFERENCE},
        "commandes_par_mois": [{"mois": str(m), "toutes": int(r["toutes"]),
                                "livrees": int(r["livrees"])} for m, r in mois.iterrows()],
        "histogrammes": histo,
        "correlations_spearman": prof[v].corr(method="spearman").round(4).to_dict(),
        "etats": prof["etat"].value_counts().to_dict(),
    }
    ecrire_json(DOSSIER / "exploration.json", exploration)
    shutil.copy(config.RACINE / "data" / "demo" / "LICENCE.md", DOSSIER / "LICENCE.md")

    tailles = {p.name: p.stat().st_size for p in DOSSIER.iterdir()}
    for nom, t in sorted(tailles.items()):
        print(f"{nom:<22} {t / 1024:8.1f} Ko")
    print(f"total : {sum(tailles.values()) / 1024:.1f} Ko")
    return 0


if __name__ == "__main__":
    sys.exit(main())
