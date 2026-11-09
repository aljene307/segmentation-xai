"""Enregistre les segments retenus (k = config.K_RETENU) : centres, noms, actions.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\enregistrer_segments.py

Les centres sont dans l'espace des 8 variables préparées (étape 3) : un nouveau client est
préparé avec models/preparation.json, puis affecté au centre le plus proche.
Sortie : models/segments.json (versionné, LF).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402
from segmentation.partitions import affecter  # noqa: E402


def main() -> int:
    proteger_sorties()
    k = config.K_RETENU
    z = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    x = z[config.VARIABLES_PROFIL].to_numpy(dtype=float)
    e = pd.read_csv(config.PARTITIONS, index_col="customer_unique_id").loc[
        z.index, f"kmeans_k{k}"].to_numpy()
    centres = np.array([x[e == s].mean(axis=0) for s in range(k)])
    accord = float((affecter(x, centres) == e).mean())
    segments = {
        "version": 1,
        "k": k,
        "methode": "K-Means sur les 8 variables préparées (20 initialisations, graine 42)",
        "variables": config.VARIABLES_PROFIL,
        "clients_apprentissage": len(x),
        "accord_affectation_apprentissage": accord,
        "segments": [
            {"id": s, "nom": config.SEGMENTS_NOMS_ACTIONS[s][0],
             "action": config.SEGMENTS_NOMS_ACTIONS[s][1],
             "clients": int((e == s).sum()), "centre": centres[s].tolist()}
            for s in range(k)
        ],
    }
    config.SEGMENTS.parent.mkdir(parents=True, exist_ok=True)
    with open(config.SEGMENTS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Segments enregistrés : models/segments.json ; réaffectation des clients "
          f"d'apprentissage identique à la partition pour {100 * accord:.4f} % d'entre eux")
    return 0


if __name__ == "__main__":
    sys.exit(main())
