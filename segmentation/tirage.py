"""Mise de côté d'une part des clients, reproductible et vérifiable.

Le tirage se fait par client : un client est entièrement d'un côté ou de l'autre.
Les identifiants sont triés avant le mélange : le résultat ne dépend pas de
l'ordre des lignes. L'empreinte SHA-256 de la liste triée mise de côté permet de
prouver plus tard que le tirage n'a pas changé, sans versionner la liste.
"""

from __future__ import annotations

import hashlib

import numpy as np


def separer(identifiants, part: float, graine: int) -> tuple[list[str], list[str]]:
    """Renvoie (apprentissage, mise_de_cote), chacune triée."""
    ids = np.array(sorted(set(identifiants)))
    n_cote = int(round(part * len(ids)))
    melange = np.random.default_rng(graine).permutation(len(ids))
    cote = np.zeros(len(ids), dtype=bool)
    cote[melange[:n_cote]] = True
    return sorted(ids[~cote].tolist()), sorted(ids[cote].tolist())


def empreinte(identifiants) -> str:
    texte = "\n".join(sorted(identifiants)).encode("utf-8")
    return hashlib.sha256(texte).hexdigest()
