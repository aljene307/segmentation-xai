"""Sorties console sûres sous Windows.

Quand la sortie d'un script est redirigée (tube, fichier, autre programme), Python
écrit dans l'encodage du système (cp1252 sous Windows), qui ne connaît pas certains
caractères (« → », « ≥ »…) : le script plantait avec UnicodeEncodeError.
Ici, un caractère impossible à écrire est remplacé par « ? » au lieu de faire planter.
"""

from __future__ import annotations

import sys


def proteger_sorties(*flux) -> None:
    for f in flux or (sys.stdout, sys.stderr):
        if hasattr(f, "reconfigure"):
            f.reconfigure(errors="replace")
