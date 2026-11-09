"""Chaîne figée de l'API : tout est lu dans les fichiers JSON de models/, rien n'est réappris.

8 variables (unités d'origine)
  → preparation.json : log(1 + x), écrêtage, standardisation
  → segments.json    : centre le plus proche → segment
  → explication.json : seuils atypiques, frontière, moyennes, médianes, arbre, phrases
  → acp.json         : coordonnées F1, F2 (carte)
Aucune dépendance à scikit-learn ni à scipy. Au démarrage, les empreintes SHA-256 des fichiers
sont comparées à models/empreintes.json : un fichier altéré empêche le démarrage.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from segmentation import acp as A
from segmentation import config
from segmentation import explication as X
from segmentation import preparation as prepa
from segmentation.geometrie import affecter

FICHIERS = ("preparation.json", "acp.json", "segments.json", "explication.json")


def empreintes(dossier: Path) -> dict[str, str]:
    return {f: hashlib.sha256((dossier / f).read_bytes()).hexdigest() for f in FICHIERS}


class Moteur:
    def __init__(self, dossier: Path = config.DOSSIER_MODELES, demo: Path | None = None):
        attendues = json.loads((dossier / "empreintes.json").read_text(encoding="utf-8"))
        reelles = empreintes(dossier)
        ecarts = [f for f in FICHIERS if attendues.get(f) != reelles[f]]
        if ecarts:
            raise RuntimeError(f"Fichiers de modèle altérés ou inattendus : {ecarts}. "
                               "Refaire un clone propre du dépôt.")
        self.empreintes = reelles
        lire = lambda f: json.loads((dossier / f).read_text(encoding="utf-8"))  # noqa: E731
        self.preparation = prepa.charger(dossier / "preparation.json")
        self.acp = A.charger(dossier / "acp.json")
        self.segments = lire("segments.json")
        self.expl = lire("explication.json")
        self.variables = self.segments["variables"]
        self.centres = np.array([s["centre"] for s in self.segments["segments"]])
        self.noms = {s["id"]: s["nom"] for s in self.segments["segments"]}
        self.actions = {s["id"]: s["action"] for s in self.segments["segments"]}
        self.seuils = self.expl["seuils_atypiques"]
        self.medianes = {int(k): v for k, v in self.expl["medianes_segments"].items()}
        self.unites = prepa.seuils_en_unites(self.preparation)
        chemin_demo = demo or (config.RACINE / "data" / "demo" / "exemples.json")
        self.exemples = (json.loads(chemin_demo.read_text(encoding="utf-8"))
                         if chemin_demo.exists() else [])

    # --- Calculs ---------------------------------------------------------------------
    def preparer(self, df: pd.DataFrame) -> np.ndarray:
        return prepa.appliquer(df, self.preparation)[self.variables].to_numpy(dtype=float)

    def affecter(self, df: pd.DataFrame) -> np.ndarray:
        """Segments d'un lot de clients (unités d'origine)."""
        return affecter(self.preparer(df), self.centres)

    def segment(self, s: int) -> dict:
        return {"id": s, "nom": self.noms[s], "action": self.actions[s]}

    def expliquer(self, valeurs: dict) -> dict:
        df = pd.DataFrame([valeurs])[self.variables]
        z = self.preparer(df)[0]
        brut = df.iloc[0]
        e = X.expliquer(z, brut, self.centres, self.seuils, self.variables,
                        self.expl["moyennes_globales"], self.medianes)
        s = e["segment"]
        ecr = prepa.ecretages(df, self.preparation).iloc[0]
        ecretees = []
        for v in self.variables:
            if ecr[v]:
                bas, haut = self.unites[v]
                ramene = bas if brut[v] < bas else haut
                ecretees.append({"variable": v, "valeur": float(brut[v]), "ramenee_a": ramene})
        numero, seg_arbre = X.regle_du_client(self.expl["arbre"], brut.to_dict())
        f = A.projeter(pd.DataFrame([z], columns=self.variables), self.acp, 2).iloc[0]

        def details(liste):
            return [{**d, "libelle": X.LIBELLES[d["variable"]][0],
                     "unite": X.LIBELLES[d["variable"]][1]} for d in liste]

        statut = "atypique" if e["atypique"] else "typique"
        texte = (f"Client affecté au segment S{s} « {self.noms[s]} » (action : "
                 f"{self.actions[s][0].lower() + self.actions[s][1:]}). Client {statut}"
                 + (f", à la frontière avec S{e['segment_2']} « {self.noms[e['segment_2']]} »"
                    if e["frontiere"] else "") + ".")
        return {
            "segment": self.segment(s),
            "distance": e["distance"], "seuil_atypique": e["seuil_atypique"],
            "atypique": e["atypique"],
            "deuxieme_segment": {"id": e["segment_2"], "nom": self.noms[e["segment_2"]]},
            "distance_2": e["distance_2"], "rapport_distances": e["distance"] / e["distance_2"],
            "seuil_frontiere": self.expl["seuil_frontiere"], "frontiere": e["frontiere"],
            "ecretees": ecretees,
            "loin_du_client_moyen": details(e["loin_du_client_moyen"]),
            "loin_du_centre_du_segment": details(e["loin_du_centre_du_segment"]),
            "regle_arbre": {"numero": numero + 1, "phrase": self.expl["regles"][numero],
                            "segment_arbre": seg_arbre, "accord": seg_arbre == s},
            "acp": {"F1": float(f["F1"]), "F2": float(f["F2"])},
            "texte": texte,
        }

    def decrire(self) -> list[dict]:
        total = self.segments["clients_apprentissage"]
        return [{**self.segment(s["id"]), "clients": s["clients"],
                 "part_clients": s["clients"] / total,
                 "part_ca": self.expl["part_ca"][str(s["id"])] / 100,
                 "indices_profil": self.expl["indices_profil"][str(s["id"])],
                 "medianes": self.medianes[s["id"]]} for s in self.segments["segments"]]
