"""Comparaison de paramètres recalculés avec ceux enregistrés, à une tolérance près.

Sur une autre machine (autre processeur, autre bibliothèque de calcul), les dernières décimales
d'un calcul flottant (vers la 16e) peuvent différer : une égalité exacte ferait échouer la
reproduction pour rien. La tolérance (10⁻⁹) reste bien plus fine que toute différence utile.
"""

from __future__ import annotations

import math

TOLERANCE = 1e-9


def presque_egaux(a, b, tol: float = TOLERANCE) -> bool:
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(presque_egaux(a[c], b[c], tol) for c in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(presque_egaux(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=tol, abs_tol=tol)
    return a == b
