"""Tests du téléchargement : extraction sûre, empreintes, manifeste (sans réseau)."""

import zipfile

import pytest

from segmentation.telechargement import (
    comparer_au_manifeste,
    extraire_sans_risque,
    inventaire,
    sha256,
)


def _zip(chemin, membres):
    with zipfile.ZipFile(chemin, "w") as z:
        for nom, contenu in membres.items():
            z.writestr(nom, contenu)
    return chemin


def test_extraction_normale(tmp_path):
    archive = _zip(tmp_path / "a.zip", {"a.csv": "x\n1\n", "b.csv": "y\n2\n"})
    noms = extraire_sans_risque(archive, tmp_path / "sortie", octets_max=10_000)
    assert noms == ["a.csv", "b.csv"]
    assert (tmp_path / "sortie" / "a.csv").read_text() == "x\n1\n"


def test_extraction_refuse_chemin_sortant(tmp_path):
    archive = _zip(tmp_path / "a.zip", {"../evasion.csv": "x"})
    with pytest.raises(ValueError, match="Chemin refusé"):
        extraire_sans_risque(archive, tmp_path / "sortie", octets_max=10_000)
    assert not (tmp_path / "evasion.csv").exists()


def test_extraction_refuse_archive_trop_grosse(tmp_path):
    archive = _zip(tmp_path / "a.zip", {"a.csv": "x" * 5_000})
    with pytest.raises(ValueError, match="trop volumineuse"):
        extraire_sans_risque(archive, tmp_path / "sortie", octets_max=1_000)


def test_sha256_valeur_connue(tmp_path):
    f = tmp_path / "f.txt"
    f.write_bytes(b"abc")
    assert sha256(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_manifeste_detecte_ecarts(tmp_path):
    (tmp_path / "a.csv").write_text("1")
    (tmp_path / "b.csv").write_text("2")
    ref = {"fichiers": inventaire(tmp_path)}
    assert comparer_au_manifeste(inventaire(tmp_path), ref) == []

    (tmp_path / "a.csv").write_text("modifié")
    (tmp_path / "b.csv").unlink()
    (tmp_path / "c.csv").write_text("3")
    ecarts = comparer_au_manifeste(inventaire(tmp_path), ref)
    assert ecarts == ["contenu différent : a.csv", "manquant : b.csv", "inattendu : c.csv"]
