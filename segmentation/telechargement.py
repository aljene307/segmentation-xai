"""Téléchargement, extraction sûre et empreintes des fichiers bruts."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import requests


def telecharger(url: str, destination: Path, morceau: int = 1 << 20) -> int:
    """Télécharge `url` dans `destination` par morceaux ; renvoie le nombre d'octets."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporaire = destination.with_suffix(destination.suffix + ".part")
    total = 0
    with requests.get(url, stream=True, timeout=60) as reponse:
        reponse.raise_for_status()
        with open(temporaire, "wb") as f:
            for bloc in reponse.iter_content(chunk_size=morceau):
                f.write(bloc)
                total += len(bloc)
    temporaire.replace(destination)
    return total


def extraire_sans_risque(archive: Path, dossier: Path, octets_max: int) -> list[str]:
    """Extrait l'archive en refusant tout chemin qui sortirait de `dossier`
    et toute archive qui dépasserait `octets_max` une fois décompressée."""
    dossier.mkdir(parents=True, exist_ok=True)
    base = dossier.resolve()
    with zipfile.ZipFile(archive) as z:
        membres = [m for m in z.infolist() if not m.is_dir()]
        if sum(m.file_size for m in membres) > octets_max:
            raise ValueError("Archive trop volumineuse une fois décompressée.")
        for m in membres:
            cible = (base / m.filename).resolve()
            if base not in cible.parents:
                raise ValueError(f"Chemin refusé dans l'archive : {m.filename!r}")
        if z.testzip() is not None:
            raise ValueError("Archive corrompue (contrôle CRC en échec).")
        for m in membres:
            z.extract(m, base)
    return sorted(m.filename for m in membres)


def sha256(chemin: Path, morceau: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(morceau), b""):
            h.update(bloc)
    return h.hexdigest()


def inventaire(dossier: Path) -> dict[str, dict]:
    """Taille et empreinte SHA-256 de chaque fichier du dossier (noms triés)."""
    return {
        p.name: {"octets": p.stat().st_size, "sha256": sha256(p)}
        for p in sorted(dossier.iterdir())
        if p.is_file()
    }


def comparer_au_manifeste(fichiers: dict[str, dict], manifeste: dict) -> list[str]:
    """Liste des écarts entre l'inventaire et le manifeste de référence."""
    ecarts = []
    attendus = manifeste["fichiers"]
    for nom in sorted(set(attendus) | set(fichiers)):
        if nom not in fichiers:
            ecarts.append(f"manquant : {nom}")
        elif nom not in attendus:
            ecarts.append(f"inattendu : {nom}")
        elif fichiers[nom]["sha256"] != attendus[nom]["sha256"]:
            ecarts.append(f"contenu différent : {nom}")
    return ecarts


def ecrire_json(chemin: Path, contenu: dict) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        json.dump(contenu, f, ensure_ascii=False, indent=2)
        f.write("\n")
