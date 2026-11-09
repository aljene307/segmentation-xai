"""Tests de la protection des sorties console (accents et symboles sous Windows)."""

import io
import subprocess
import sys

import pytest

from segmentation import config
from segmentation.console import proteger_sorties

TEXTE = "Délai → 30 j ≥ 99e centile (R$)"


def test_flux_cp1252_ne_plante_plus():
    flux = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    proteger_sorties(flux)
    flux.write(TEXTE)  # sans protection : UnicodeEncodeError
    flux.flush()
    assert flux.buffer.getvalue().decode("cp1252") == "Délai ? 30 j ? 99e centile (R$)"


@pytest.mark.skipif(sys.platform != "win32", reason="cas propre à Windows (tube en cp1252)")
def test_sortie_redirigee_dans_un_autre_processus():
    """Reproduit le cas réel : sortie capturée par un tube, encodage du système (cp1252)."""
    code = (
        "import sys; sys.path.insert(0, {racine!r});"
        "from segmentation.console import proteger_sorties;"
        "proteger_sorties(); print({texte!r})"
    ).format(racine=str(config.RACINE), texte=TEXTE)
    r = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("cp1252", "replace")
    assert r.stdout.decode("cp1252").startswith("Délai ? 30 j")


@pytest.mark.skipif(sys.platform != "win32", reason="cas propre à Windows (tube en cp1252)")
def test_sans_protection_le_probleme_existe_bien():
    """Témoin : sans proteger_sorties, le même affichage plante."""
    r = subprocess.run([sys.executable, "-I", "-c", f"print({TEXTE!r})"], capture_output=True)
    assert r.returncode != 0 and b"UnicodeEncodeError" in r.stderr
