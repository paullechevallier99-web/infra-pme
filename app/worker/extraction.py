"""Extraction des informations clés d'une facture PDF, et calcul de son rangement.

Volontairement simple et vérifiable : texte extrait par pypdf, puis expressions
régulières. Une facture dont une information manque est classée « a_verifier »,
jamais perdue.
"""
import io
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

from pypdf import PdfReader

MOIS = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
        "décembre": 12, "decembre": 12}

RE_SIRET = re.compile(r"\b(\d{3}\s?\d{3}\s?\d{3}\s?\d{5})\b")
RE_DATE_FR = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b")
RE_DATE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
RE_DATE_LONGUE = re.compile(r"\b(\d{1,2})\s+(" + "|".join(MOIS) + r")\s+(\d{4})\b", re.IGNORECASE)
RE_TOTAL = re.compile(
    r"(?:total\s*ttc|net\s*[àa]\s*payer|montant\s*ttc|total\s*[àa]\s*payer)\s*:?\s*"
    r"(\d{1,3}(?:[ \u00a0\u202f.]\d{3})*(?:[.,]\d{2})|\d+(?:[.,]\d{2})?)",
    re.IGNORECASE,
)
RE_NUMERO = re.compile(
    r"(?:facture\s*(?:n[°o]|num[ée]ro)|n[°o]\s*(?:de\s*)?facture)\s*:?\s*([A-Z0-9][A-Z0-9/_-]{2,30})",
    re.IGNORECASE,
)


@dataclass
class Resultat:
    siret: str | None = None
    date_facture: date | None = None
    montant_ttc: Decimal | None = None
    numero: str | None = None
    manquants: list[str] = field(default_factory=list)

    @property
    def classement(self) -> str:
        return "classee" if not self.manquants else "a_verifier"

    def dossier(self) -> str:
        """Chemin relatif du rangement : classees/AAAA/MM/SIRET ou a_verifier."""
        if self.classement != "classee":
            return "a_verifier"
        return f"classees/{self.date_facture:%Y/%m}/{self.siret}"


def siret_valide(siret: str) -> bool:
    """Contrôle de Luhn, utilisé par l'INSEE pour les SIREN et SIRET."""
    if len(siret) != 14 or not siret.isdigit():
        return False
    total = 0
    for i, c in enumerate(reversed(siret)):
        n = int(c) * (2 if i % 2 else 1)
        total += n - 9 if n > 9 else n
    return total % 10 == 0


def texte_du_pdf(data: bytes, max_pages: int = 5) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = reader.pages[:max_pages]
    return "\n".join((p.extract_text() or "") for p in pages)


def _montant(brut: str) -> Decimal | None:
    s = brut.replace("\u00a0", "").replace("\u202f", "").replace(" ", "")
    if "," in s:                       # format français : 1.234,56
        s = s.replace(".", "").replace(",", ".")
    elif s.count(".") > 1:             # 1.234.567 sans décimales
        s = s.replace(".", "")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _premiere_date(texte: str) -> date | None:
    candidats = []
    for m in RE_DATE_FR.finditer(texte):
        candidats.append((m.start(), int(m.group(3)), int(m.group(2)), int(m.group(1))))
    for m in RE_DATE_ISO.finditer(texte):
        candidats.append((m.start(), int(m.group(1)), int(m.group(2)), int(m.group(3))))
    for m in RE_DATE_LONGUE.finditer(texte):
        candidats.append((m.start(), int(m.group(3)), MOIS[m.group(2).lower()], int(m.group(1))))
    for _, a, mo, j in sorted(candidats):
        try:
            d = date(a, mo, j)
        except ValueError:
            continue
        if 2000 <= d.year <= 2100:
            return d
    return None


def analyser(texte: str) -> Resultat:
    r = Resultat()
    for m in RE_SIRET.finditer(texte):
        candidat = re.sub(r"\s", "", m.group(1))
        if siret_valide(candidat):
            r.siret = candidat
            break
    r.date_facture = _premiere_date(texte)
    totaux = [_montant(m.group(1)) for m in RE_TOTAL.finditer(texte)]
    totaux = [t for t in totaux if t is not None]
    if totaux:
        r.montant_ttc = totaux[-1]     # le dernier total de la facture est le total final
    m = RE_NUMERO.search(texte)
    if m:
        r.numero = m.group(1)
    r.manquants = [nom for nom, val in (("siret", r.siret), ("date", r.date_facture),
                                        ("montant", r.montant_ttc)) if val is None]
    return r


def analyser_pdf(data: bytes) -> Resultat:
    try:
        texte = texte_du_pdf(data)
    except Exception:                  # PDF illisible : à vérifier par un humain
        return Resultat(manquants=["texte"])
    if not texte.strip():              # PDF scanné, sans couche texte
        return Resultat(manquants=["texte"])
    return analyser(texte)
