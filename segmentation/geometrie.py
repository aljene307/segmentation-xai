"""Calculs de distances, sans scikit-learn (utilisés par les analyses ET par l'API)."""

from __future__ import annotations

import numpy as np


def distances(x: np.ndarray, centres: np.ndarray) -> np.ndarray:
    """Distances euclidiennes de chaque ligne de x à chaque centre."""
    return np.sqrt(((x[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2))


def affecter(x: np.ndarray, centres: np.ndarray) -> np.ndarray:
    """Chaque ligne va au centre le plus proche (distance euclidienne)."""
    d = ((x[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2)
    return d.argmin(axis=1)
