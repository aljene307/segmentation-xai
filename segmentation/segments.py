"""Segments officiels : affectation au centre le plus proche de models/segments.json.

C'est exactement ce que fera l'API pour un nouveau client : préparation (étape 3), puis
centre le plus proche dans l'espace des 8 variables préparées.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from segmentation import config
from segmentation.geometrie import affecter


def charger(chemin: Path = config.SEGMENTS) -> dict:
    s = json.loads(Path(chemin).read_text(encoding="utf-8"))
    if s.get("version") != 1:
        raise ValueError(f"Version de segments inattendue : {s.get('version')}")
    return s


def centres(segments: dict) -> np.ndarray:
    return np.array([seg["centre"] for seg in segments["segments"]])


def affecter_prepares(z: pd.DataFrame, segments: dict) -> pd.Series:
    """Segment officiel de clients déjà préparés (colonnes = les 8 variables)."""
    manquantes = [v for v in segments["variables"] if v not in z.columns]
    if manquantes:
        raise ValueError(f"Variables manquantes : {manquantes}")
    x = z[segments["variables"]].to_numpy(dtype=float)
    return pd.Series(affecter(x, centres(segments)), index=z.index, name="segment")


def segments_apprentissage() -> pd.Series:
    """Segment officiel des clients d'apprentissage (fichier écrit par enregistrer_segments.py)."""
    return pd.read_csv(config.SEGMENTS_APPRENTISSAGE, index_col="customer_unique_id")["segment"]
