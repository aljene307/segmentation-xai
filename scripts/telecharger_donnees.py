"""Télécharge le jeu Olist depuis Kaggle, l'extrait et vérifie ses empreintes.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\telecharger_donnees.py
    .venv\\Scripts\\python -I scripts\\telecharger_donnees.py --zip chemin\\archive.zip

Premier lancement : écrit le manifeste de référence docs/donnees_manifeste.json.
Lancements suivants : compare les fichiers à ce manifeste et s'arrête en cas d'écart.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation.telechargement import (  # noqa: E402
    comparer_au_manifeste,
    ecrire_json,
    extraire_sans_risque,
    inventaire,
    telecharger,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--zip", type=Path, help="archive déjà téléchargée à la main")
    args = parser.parse_args()

    if args.zip:
        config.DOSSIER_RAW.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.zip, config.FICHIER_ZIP)
        print(f"Archive importée : {args.zip.name}")
    elif config.FICHIER_ZIP.exists():
        print("Archive déjà présente, pas de nouveau téléchargement.")
    else:
        print("Téléchargement depuis Kaggle…")
        n = telecharger(config.URL_KAGGLE, config.FICHIER_ZIP)
        print(f"  {n:,} octets reçus (archive compressée)".replace(",", " "))

    if config.DOSSIER_OLIST.exists():
        shutil.rmtree(config.DOSSIER_OLIST)
    noms = extraire_sans_risque(
        config.FICHIER_ZIP, config.DOSSIER_OLIST, config.OCTETS_MAX_EXTRACTION
    )
    print(f"Extraction : {len(noms)} fichiers dans data/raw/olist/")

    fichiers = inventaire(config.DOSSIER_OLIST)
    total = sum(f["octets"] for f in fichiers.values())
    print(f"\n{'Fichier':<45}{'Octets':>14}  SHA-256 (début)")
    for nom, info in fichiers.items():
        print(f"{nom:<45}{info['octets']:>14,}  {info['sha256'][:16]}…".replace(",", " "))
    egal = "OUI" if total == config.OCTETS_ANNONCES else "NON"
    print(f"\nTotal décompressé : {total:,} octets".replace(",", " "))
    print(f"Annoncé par Kaggle : {config.OCTETS_ANNONCES:,} octets".replace(",", " "))
    print(f"Identique : {egal}")

    if config.MANIFESTE.exists():
        manifeste = json.loads(config.MANIFESTE.read_text(encoding="utf-8"))
        ecarts = comparer_au_manifeste(fichiers, manifeste)
        if ecarts:
            print("\nÉCART avec le manifeste de référence :")
            for e in ecarts:
                print(f"  - {e}")
            return 1
        print("\nManifeste de référence : tous les fichiers sont identiques.")
    else:
        ecrire_json(
            config.MANIFESTE,
            {
                "source": config.PAGE_KAGGLE,
                "licence": config.LICENCE,
                "date_telechargement": date.today().isoformat(),
                "octets_total": total,
                "fichiers": fichiers,
            },
        )
        print("\nManifeste de référence écrit : docs/donnees_manifeste.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
