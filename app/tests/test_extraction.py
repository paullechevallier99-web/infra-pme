"""Tests du classement : ils tournent sans base de données ni Redis."""
from datetime import date
from decimal import Decimal

import pytest

from worker.extraction import analyser, analyser_pdf, siret_valide

FACTURE = """FOURNITURES DUPONT SAS
SIRET : 732 829 320 00074
Facture N° FA-2026-0142
Date : 03/11/2026
Total HT                      37,50
TVA 20 %                       7,50
Total TTC                     45,00
"""


def test_siret_luhn():
    assert siret_valide("73282932000074")
    assert not siret_valide("73282932000075")
    assert not siret_valide("1234")


def test_facture_complete():
    r = analyser(FACTURE)
    assert r.siret == "73282932000074"
    assert r.date_facture == date(2026, 11, 3)
    assert r.montant_ttc == Decimal("45.00")
    assert r.numero == "FA-2026-0142"
    assert r.dossier() == "classees/2026/11/73282932000074"


def test_formats_varies():
    r = analyser("SIRET 44306184100047\nle 5 novembre 2026\nNet à payer : 1 234,56 €")
    assert r.date_facture == date(2026, 11, 5)
    assert r.montant_ttc == Decimal("1234.56")
    assert r.classement == "classee"


def test_siret_invalide_ignore():
    r = analyser("SIRET 12345678901234\nDate 01/01/2026\nTotal TTC 10,00")
    assert r.siret is None
    assert r.dossier() == "a_verifier"


def test_pdf_sans_texte():
    assert analyser_pdf(b"%PDF-1.4\nfacture de test\n%%EOF\n").classement == "a_verifier"


def test_pdf_reel(tmp_path):
    canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    chemin = tmp_path / "f.pdf"
    c = canvas.Canvas(str(chemin))
    for i, ligne in enumerate(FACTURE.splitlines()):
        c.drawString(50, 800 - 16 * i, ligne)
    c.save()
    r = analyser_pdf(chemin.read_bytes())
    assert r.classement == "classee"
    assert r.montant_ttc == Decimal("45.00")
