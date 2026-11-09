"""Étape 6 (module 5) : profils, arbre de substitution, explication des clients.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\expliquer_segments.py

Règles fixées et poussées avant le calcul (docs/CHOIX.md). Aucun avis n'est lu.
Sorties :
    models/explication.json   (versionné, LF)
    reports/explication.md    (versionné)
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation import explication as X  # noqa: E402
from segmentation import segments as S  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402


def tableau(entetes, lignes):
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    return "\n".join(out + ["| " + " | ".join(map(str, l)) + " |" for l in lignes])


def pct(v, d=1):
    return X.nombre(100 * v, d) + " %"


def main() -> int:
    proteger_sorties()
    v = config.VARIABLES_PROFIL
    segs = S.charger()
    centres = S.centres(segs)
    k = segs["k"]
    noms = {s["id"]: s["nom"] for s in segs["segments"]}

    prof80 = pd.read_csv(config.PROFILS_APPRENTISSAGE, index_col="customer_unique_id")
    prof20 = pd.read_csv(config.PROFILS_MISE_DE_COTE, index_col="customer_unique_id")
    z80 = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    z20 = pd.read_csv(config.PREPARES_MISE_DE_COTE, index_col="customer_unique_id")
    prof80, prof20 = prof80.loc[z80.index], prof20.loc[z20.index]
    seg80 = S.segments_apprentissage().loc[z80.index]
    seg20 = S.affecter_prepares(z20, segs)

    # 1. Profils
    ip = X.indices_profil(prof80, seg80, v)
    ca = X.part_ca(prof80, seg80)
    med = prof80[v].groupby(seg80).median()
    moy = prof80[v].mean()

    def principaux(col, n):
        return {s: ", ".join(f"{c} ({100 * p:.0f} %)" for c, p in
                             prof80.loc[seg80 == s, col].value_counts(normalize=True)
                             .head(n).items()) for s in range(k)}

    etats, paiement, categories = (principaux("etat", 3), principaux("paiement_principal", 1),
                                   principaux("categorie_principale", 3))

    # 2. Arbres de profondeur 3 et 4
    feuille_min = math.ceil(0.01 * len(z80))
    arbres, fid = {}, {}
    for p in (3, 4):
        a = X.apprendre_arbre(prof80[v], seg80, p, feuille_min, config.GRAINE)
        arbres[p] = a
        fid[p] = {"80": float((X.predire_arbre(a, prof80) == seg80.to_numpy()).mean()),
                  "20": float((X.predire_arbre(a, prof20) == seg20.to_numpy()).mean())}
    p = X.choisir_profondeur(fid[3]["80"], fid[4]["80"])
    arbre = arbres[p]
    pred80, pred20 = X.predire_arbre(arbre, prof80), X.predire_arbre(arbre, prof20)
    regles = X.regles(arbre)
    phrases = [X.phrase(r, noms) for r in regles]

    def confusion(vrai, pred):
        c = pd.crosstab(pd.Series(vrai, name="officiel"), pd.Series(pred, name="arbre"),
                        normalize="index").reindex(index=range(k), columns=range(k), fill_value=0)
        return [[f"S{s}"] + [pct(c.loc[s, t]) for t in range(k)] for s in range(k)]

    # 3. Atypiques et frontière
    seuils = X.seuils_atypiques(z80[v].to_numpy(), seg80.to_numpy(), centres)
    d80 = X.diagnostic(z80[v].to_numpy(), centres, seuils)
    d20 = X.diagnostic(z20[v].to_numpy(), centres, seuils)
    medianes = {s: {c: float(med.loc[s, c]) for c in v} for s in range(k)}
    moyennes = {c: float(moy[c]) for c in v}

    # 4. Deux exemples (clients mis de côté, traités comme de nouveaux clients ; ordre fixe)
    ordre = sorted(z20.index)
    d20.index = z20.index
    ex_a = next(i for i in ordre if d20.loc[i, "segment"] == 2 and not d20.loc[i, "atypique"]
                and not d20.loc[i, "frontiere"])
    ex_b = next(i for i in ordre if d20.loc[i, "atypique"])
    exemples = {nom: X.expliquer(z20.loc[i, v].to_numpy(dtype=float), prof20.loc[i], centres,
                                 seuils, v, moyennes, medianes)
                for nom, i in (("Client A", ex_a), ("Client B", ex_b))}

    # --- Enregistrement ---------------------------------------------------------------
    explication = {
        "version": 1, "variables": v, "segments": noms,
        "seuil_frontiere": X.SEUIL_FRONTIERE, "centile_atypique": X.CENTILE_ATYPIQUE,
        "seuils_atypiques": seuils, "moyennes_globales": moyennes, "medianes_segments": medianes,
        "indices_profil": {int(s): {c: float(ip.loc[s, c]) for c in v} for s in range(k)},
        "part_ca": {int(s): float(ca[s]) for s in range(k)},
        "arbre": {**arbre, "fidelite_80": fid[p]["80"], "fidelite_20": fid[p]["20"],
                  "feuille_min": feuille_min},
        "regles": phrases,
    }
    with open(config.DOSSIER_MODELES / "explication.json", "w", encoding="utf-8",
              newline="\n") as f:
        json.dump(explication, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # --- Rapport -------------------------------------------------------------------------
    lib = {c: X.LIBELLES[c][0] for c in v}
    md = ["# Explicabilité des segments (module 5)", "",
          "Rapport généré par `scripts/expliquer_segments.py`. Règles fixées et poussées avant le "
          "calcul (voir `docs/CHOIX.md`). Segments officiels (centre le plus proche). Aucun avis "
          "lu. Montants en R$.", "",
          "## 1. Profils des segments (80 %)", "",
          "Indice de profil = moyenne du segment / moyenne globale (au moins 1,20 : nettement "
          "au-dessus ; au plus 0,80 : nettement en dessous). **Écart à la date promise : "
          "différence en jours** (moyenne du segment − moyenne globale).", "",
          tableau(["segment", "clients", "part du CA"] + [lib[c] for c in v],
                  [[f"S{s} {noms[s]}", f"{int((seg80 == s).sum())} ({pct((seg80 == s).mean())})",
                    pct(ca[s] / 100)]
                   + [(X.nombre(ip.loc[s, c], 1) + " j" if c == X.VARIABLE_EN_DIFFERENCE
                       else X.nombre(ip.loc[s, c], 2)) for c in v] for s in range(k)]), "",
          "Médianes (unités d'origine) :", "",
          tableau(["segment"] + [lib[c] for c in v],
                  [[f"S{s}"] + [X.avec_unite(c, med.loc[s, c]) for c in v] for s in range(k)]
                  + [["moyenne globale"] + [X.avec_unite(c, moy[c]) for c in v]]), "",
          tableau(["segment", "3 États principaux", "paiement principal", "3 catégories principales"],
                  [[f"S{s}", etats[s], paiement[s], categories[s]] for s in range(k)]), "",
          "## 2. Arbre de décision de substitution", "",
          f"Variables en unités d'origine ; au moins {feuille_min} clients par feuille ; graine "
          f"{config.GRAINE}. Fidélité = part des clients pour lesquels l'arbre donne le segment "
          "officiel.", "",
          tableau(["profondeur", "fidélité 80 %", "fidélité 20 %", "feuilles"],
                  [[q, pct(fid[q]["80"], 2), pct(fid[q]["20"], 2), len(X.regles(arbres[q]))]
                   for q in (3, 4)]), "",
          f"**Règle** : profondeur 3 si sa fidélité sur les 80 % atteint 90 % ; sinon 4 si elle "
          f"gagne au moins 3 points ; sinon 3. **Profondeur retenue : {p}.**", "",
          "Fidélité par segment et confusions (lignes : segment officiel ; colonnes : segment "
          "donné par l'arbre ; en % de la ligne) :", "",
          "**80 %**", "", tableau(["officiel \\ arbre"] + [f"S{t}" for t in range(k)],
                                   confusion(seg80.to_numpy(), pred80)), "",
          "**20 %**", "", tableau(["officiel \\ arbre"] + [f"S{t}" for t in range(k)],
                                   confusion(seg20.to_numpy(), pred20)), "",
          f"**À lire avec l'arbre (hors de l'arbre)** : S4 « {noms[4]} » est exactement "
          "l'ensemble des clients à au moins 2 commandes : la règle « le client a au moins "
          f"2 commandes » le retrouve à {pct(((prof80['frequence'] >= 2) == (seg80 == 4)).mean())} "
          f"(80 %). L'arbre ne le retrouve qu'à {pct((pred80[seg80.to_numpy() == 4] == 4).mean())}, "
          "car il cherche la meilleure fidélité globale et ne teste le nombre de commandes qu'au "
          "quatrième niveau d'une seule branche.", "",
          "### Règles en phrases", ""]
    md += [f"{i}. {ph}" for i, ph in enumerate(phrases, 1)]
    md += ["", "## 3. Clients atypiques et à la frontière", "",
           "Atypique : distance au centre de son segment au-delà du 95e centile des clients "
           "d'apprentissage de ce segment. À la frontière : distance au centre de son segment "
           "≥ 90 % de la distance au 2e centre.", "",
           tableau(["segment", "seuil atypique (distance)", "atypiques 80 %", "atypiques 20 %",
                    "à la frontière 80 %", "à la frontière 20 %"],
                   [[f"S{s}", X.nombre(seuils[s], 3),
                     pct(d80.loc[d80["segment"] == s, "atypique"].mean()),
                     pct(d20.loc[d20["segment"] == s, "atypique"].mean()),
                     pct(d80.loc[d80["segment"] == s, "frontiere"].mean()),
                     pct(d20.loc[d20["segment"] == s, "frontiere"].mean())] for s in range(k)]
                   + [["**tous**", "", pct(d80["atypique"].mean()), pct(d20["atypique"].mean()),
                       pct(d80["frontiere"].mean()), pct(d20["frontiere"].mean())]]), "",
           "## 4. Deux clients expliqués (clients mis de côté, traités comme de nouveaux "
           "clients)", ""]
    for nom, e in exemples.items():
        s = e["segment"]
        md += [f"### {nom}", "",
               f"- Segment : **S{s} « {noms[s]} »** ; distance au centre "
               f"{X.nombre(e['distance'], 3)} (seuil atypique {X.nombre(e['seuil_atypique'], 3)}) "
               f"→ **{'atypique' if e['atypique'] else 'typique'}**.",
               f"- 2e segment le plus proche : S{e['segment_2']} « {noms[e['segment_2']]} » "
               f"(distance {X.nombre(e['distance_2'], 3)} ; rapport "
               f"{X.nombre(e['distance'] / e['distance_2'], 2)}) → "
               f"**{'à la frontière' if e['frontiere'] else 'pas à la frontière'}**.", ""]
        for cle, titre in (("loin_du_client_moyen",
                            "Ce qui explique son segment : les 3 variables qui l'éloignent le "
                            "plus du client moyen"),
                           ("loin_du_centre_du_segment",
                            "Ce qui explique s'il est atypique : les 3 variables qui l'éloignent "
                            "le plus du centre de son segment")):
            md += [f"**{titre}**", "",
                   tableau(["variable", "part de l'écart", "sens", "valeur du client",
                            "moyenne globale", "médiane du segment"],
                           [[lib[d["variable"]], pct(d["part"]), d["sens"],
                             X.avec_unite(d["variable"], d["valeur"]),
                             X.avec_unite(d["variable"], d["moyenne_globale"]),
                             X.avec_unite(d["variable"], d["mediane_segment"])]
                            for d in e[cle]]), ""]
    (config.DOSSIER_RAPPORTS / "explication.md").write_text("\n".join(md), encoding="utf-8",
                                                            newline="\n")
    print(f"Profondeur retenue : {p} ; fidélité 80 % {fid[p]['80']:.4f}, 20 % {fid[p]['20']:.4f}")
    print("Rapport : reports/explication.md ; modèle : models/explication.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
