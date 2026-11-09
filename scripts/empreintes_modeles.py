"""Écrit models/empreintes.json : empreintes SHA-256 des fichiers de modèle lus par l'API.

Usage : .venv\\Scripts\\python -I scripts\\empreintes_modeles.py
L'API compare ces empreintes au démarrage et refuse de démarrer si un fichier diffère
(fichier altéré, converti en CRLF, tronqué…). À relancer après toute régénération d'un modèle.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.moteur import empreintes  # noqa: E402
from segmentation import config  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402
from segmentation.telechargement import ecrire_json  # noqa: E402


def main() -> int:
    proteger_sorties()
    e = empreintes(config.DOSSIER_MODELES)
    ecrire_json(config.DOSSIER_MODELES / "empreintes.json", e)
    for f, h in e.items():
        print(f"{f:<20} {h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
