"""Enregistre les segments retenus (k = config.K_RETENU) et la partition officielle des 80 %.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\enregistrer_segments.py

1. Centres = moyennes des segments de la partition K-Means de référence (sur laquelle k a
   été choisi), dans l'espace des 8 variables préparées ; noms et actions.
2. Segment officiel de chaque client d'apprentissage = centre le plus proche de ces centres,
   exactement comme l'API le fera pour un nouveau client.
Sorties :
    models/segments.json                       (versionné, LF)
    data/processed/segments_apprentissage.csv  (non versionné)
    reports/segments_officiels.md              (versionné : comparaison avec K-Means)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation import segments as S  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402


def tableau(entetes, lignes):
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    return "\n".join(out + ["| " + " | ".join(map(str, l)) + " |" for l in lignes])


def main() -> int:
    proteger_sorties()
    k = config.K_RETENU
    z = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    x = z[config.VARIABLES_PROFIL].to_numpy(dtype=float)
    km = pd.read_csv(config.PARTITIONS, index_col="customer_unique_id").loc[
        z.index, f"kmeans_k{k}"]
    centres = np.array([x[km.to_numpy() == s].mean(axis=0) for s in range(k)])

    segments = {
        "version": 1, "k": k,
        "methode": "K-Means sur les 8 variables préparées (20 initialisations, graine 42) ; "
                   "segment = centre le plus proche",
        "variables": config.VARIABLES_PROFIL,
        "clients_apprentissage": len(x),
        "segments": [{"id": s, "nom": config.SEGMENTS_NOMS_ACTIONS[s][0],
                      "action": config.SEGMENTS_NOMS_ACTIONS[s][1],
                      "centre": centres[s].tolist()} for s in range(k)],
    }
    officiel = S.affecter_prepares(z, segments)
    change = officiel != km
    segments["accord_avec_kmeans"] = float(1 - change.mean())
    for seg in segments["segments"]:
        seg["clients"] = int((officiel == seg["id"]).sum())
    with open(config.SEGMENTS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
        f.write("\n")
    pd.DataFrame({"segment": officiel, "segment_kmeans": km}).to_csv(
        config.SEGMENTS_APPRENTISSAGE, encoding="utf-8", lineterminator="\n")

    # Comparaison des profils (médianes, unités d'origine).
    prof = pd.read_csv(config.PROFILS_APPRENTISSAGE, index_col="customer_unique_id").loc[z.index]
    v = config.VARIABLES_PROFIL
    med_km = prof.groupby(km)[v].median()
    med_of = prof.groupby(officiel)[v].median()
    ecart_rel = ((med_of - med_km).abs() / med_km.abs().replace(0, np.nan)).max().max()
    ca = lambda e: 100 * prof.groupby(e)["montant_rs"].sum() / prof["montant_rs"].sum()  # noqa
    transitions = pd.crosstab(km[change], officiel[change])

    md = ["# Segments officiels : centre le plus proche", "",
          "Rapport généré par `scripts/enregistrer_segments.py`. Le segment officiel d'un client "
          "d'apprentissage est le centre le plus proche de `models/segments.json`, comme pour un "
          "nouveau client dans l'API. Comparaison avec la partition K-Means de référence (celle "
          "sur laquelle k a été choisi).", "",
          f"**Clients qui changent de segment : {int(change.sum())} sur {len(z)} "
          f"({100 * change.mean():.4f} %).**", "",
          "Transitions (lignes : segment K-Means ; colonnes : segment officiel) :", "",
          tableau(["K-Means \\ officiel"] + [f"S{c}" for c in transitions.columns],
                  [[f"S{r}"] + list(row) for r, row in transitions.iterrows()]), "",
          tableau(["segment", "clients K-Means", "clients officiels", "part du CA K-Means (%)",
                   "part du CA officielle (%)"],
                  [[f"S{s} {config.SEGMENTS_NOMS_ACTIONS[s][0]}", int((km == s).sum()),
                    int((officiel == s).sum()), f"{ca(km)[s]:.2f}", f"{ca(officiel)[s]:.2f}"]
                   for s in range(k)]), "",
          "Médianes des 8 variables avec la partition officielle (unités d'origine, R$) :", "",
          tableau(["segment"] + v,
                  [[f"S{s}"] + [f"{med_of.loc[s, c]:.2f}" for c in v] for s in range(k)]), "",
          f"Plus grand écart relatif entre les médianes K-Means et officielles : "
          f"{100 * ecart_rel:.3f} %.", ""]
    (config.DOSSIER_RAPPORTS / "segments_officiels.md").write_text(
        "\n".join(md), encoding="utf-8", newline="\n")
    print(f"Clients qui changent : {int(change.sum())} ; écart relatif max des médianes : "
          f"{100 * ecart_rel:.3f} %")
    return 0


if __name__ == "__main__":
    sys.exit(main())
