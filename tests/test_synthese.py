"""Test de la synthèse PDF (versionnée dans reports/)."""

from segmentation import config

PDF = config.RACINE / "reports" / "synthese.pdf"


def test_synthese_pdf_presente_et_de_deux_pages():
    octets = PDF.read_bytes()
    assert octets.startswith(b"%PDF")
    assert octets.count(b"/Type /Page\n") + octets.count(b"/Type /Page ") \
        + octets.count(b"/Type /Page>") >= 2
    assert len(octets) < 1024 * 1024
