"""Reading the DOSAGE and CONDITIONNEMENT columns of the nomenclature.

Both columns are free text written by hand over many years, so they carry every
spelling the ministry has ever used: ``500MG``, ``325MG/37,5MG``, ``1G/125MG``,
``250MG/5ML``, ``0,03``, ``B/16``, ``B/FL 15 ML``.

Two rules run through this module:

1. **The original text is never thrown away.** Every result keeps its ``raw``
   value, so a citation can always quote exactly what the source said.
2. **Nothing is invented.** A dosage that cannot be parsed yields an empty
   component list rather than a guess, and the caller can see that it failed.
   A wrong dose is far worse than a missing one.

No unit conversion happens here. Deciding that ``1G`` and ``1000MG`` are the
same quantity is a pharmaceutical judgement, and the project's rules forbid the
system from making it alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

__all__ = [
    "Component",
    "Strength",
    "Packaging",
    "parse_strength",
    "parse_packaging",
    "normalize_unit",
]

# Spellings met in the nomenclature, mapped to one canonical form.
_UNITS: dict[str, str] = {
    "MG": "mg", "G": "g", "GR": "g", "KG": "kg",
    "MCG": "µg", "UG": "µg", "µG": "µg", "MICROGRAMME": "µg",
    "ML": "ml", "L": "l", "CL": "cl",
    "UI": "UI", "U": "UI", "MUI": "MUI",
    "%": "%", "POURCENT": "%",
    "MEQ": "mEq", "MMOL": "mmol",
}

_NUMBER = r"\d+(?:[.,]\d+)?"
# A trailing '*' is a footnote marker used by the ministry (e.g. "875MG*/125MG*"),
# not part of the quantity. It is stripped, and the raw text keeps it.
_COMPONENT_RE = re.compile(
    rf"^\s*(?P<value>{_NUMBER})\s*(?P<unit>[A-Za-zµ%]+)?\s*\**\s*$"
)

# Mots designant un contenant dont le nombre qui suit est un nombre d'UNITES.
# Mesure sur les 5 423 conditionnements de la nomenclature d'aout 2026 : la
# seule forme "B/N" couvre 53,1 %. Y ajouter les autres contenants et le mot
# d'unite facultatif qui suit porte la couverture a 56,1 %, soit 159 produits.
_CONTENANTS = r"B|BTE|BOITE|PILULIER|PLQ|PLAQUETTE"

# Mots d'unite denombrable toleres apres le nombre : "B/30 SACHETS" vaut 30.
# Un poids ou un volume ne figure PAS ici : "T/15G" est 15 grammes de pommade,
# pas 15 unites, et "FL/5ML" un flacon de 5 ml.
_DENOMBRABLES = (
    r"SACHETS?|COMPRIMES?|CP|GELULES?|CAPSULES?|SUPPOSITOIRES?|OVULES?"
    r"|AMPOULES?|AMP|PILULES?|STICKS?|DOSES?|UNITES?"
)

# "B/16", "BTE/20", "BOITE DE 30", "PILULIER/30", "B/30 SACHETS", "B/30SACHETS".
# Le $ final est essentiel : il fait echouer "B/30 ET B/90", ou deux tailles de
# boite coexistent et ou choisir serait inventer.
_PACK_COUNT_RE = re.compile(
    rf"^\s*(?:{_CONTENANTS})\s*(?:/|\s+DE\s+)\s*(?P<count>\d+)"
    rf"\s*(?:{_DENOMBRABLES})?\s*$",
    re.I,
)
# Contenants dont le contenu se mesure, et non se compte.
_CONTENANTS_MESURE = r"FL|FLACON|F|T|TUBE|AMP|AMPOULE|SACHET|POT|SERINGUE"
_UNITES_MESURE = r"ML|L|G|MG|KG"

# "B/FL 15 ML", "B/ FL. 60ML" : la boite annonce son contenant puis sa mesure.
_PACK_VOLUME_RE = re.compile(
    rf"^\s*B\s*(?:TE|OITE)?\s*/\s*(?P<container>{_CONTENANTS_MESURE})\.?\s*"
    rf"(?P<value>{_NUMBER})\s*(?P<unit>{_UNITES_MESURE})\s*$",
    re.I,
)

# Forme A : le contenant porte directement sa mesure, sans boite.
# "T/30G", "FL/30ML", "FL/125 ML", "TUBE/30G", "FL./100ML", "F/5ML".
# Mesure sur les 911 produits des 38 molecules : 77 cas, la famille la plus
# frequente parmi les conditionnements que l'ancienne regle laissait de cote.
_PACK_MESURE_SEULE_RE = re.compile(
    rf"^\s*(?P<container>{_CONTENANTS_MESURE})\.?\s*/\s*"
    rf"(?P<value>{_NUMBER})\s*(?P<unit>{_UNITES_MESURE})\s*$",
    re.I,
)

# Forme B : une boite de N contenants, chacun d'une mesure donnee.
# "B/05 AMP. DE 2ML", "B/01 FL DE 60ML", "BOITE DE 01 FLACON DE 60ML".
# Mesure : 34 cas. Elle porte DEUX informations -- le nombre d'ampoules ET le
# volume de chacune -- la ou les autres formes n'en portent qu'une. Les
# confondre ferait lire "5 ampoules de 2 ml" comme "5 ml".
_PACK_COMPTE_ET_MESURE_RE = re.compile(
    r"^\s*B\s*(?:TE|OITE)?\s*(?:/|\s+DE\s+)\s*(?P<count>\d+)\s*"
    rf"(?P<container>{_CONTENANTS_MESURE})\.?\s*(?:DE)?\s*"
    rf"(?P<value>{_NUMBER})\s*(?P<unit>{_UNITES_MESURE})\s*$",
    re.I,
)


def _to_float(text: str) -> float:
    """French decimals use a comma: '37,5' is 37.5."""
    return float(text.replace(",", "."))


def normalize_unit(raw: str | None) -> str:
    """Map a unit spelling to its canonical form; unknown units pass through."""
    if not raw:
        return ""
    key = raw.strip().upper()
    return _UNITS.get(key, raw.strip().lower())


@dataclass(frozen=True)
class Component:
    """One quantity inside a dosage, e.g. the 125MG of ``1G/125MG``."""

    value: float
    unit: str

    def __str__(self) -> str:
        number = int(self.value) if float(self.value).is_integer() else self.value
        return f"{number}{self.unit}" if self.unit else str(number)


@dataclass(frozen=True)
class Strength:
    """A parsed DOSAGE cell."""

    raw: str
    components: tuple[Component, ...] = ()
    unparsed: tuple[str, ...] = field(default=())

    @property
    def is_combination(self) -> bool:
        """True when the product holds more than one active quantity."""
        return len(self.components) > 1

    @property
    def parsed(self) -> bool:
        """False when nothing could be read — the caller must not invent a value."""
        return bool(self.components)

    def canonical(self) -> str:
        """A stable key for grouping equivalents: '500mg', '1g+125mg'."""
        return "+".join(str(c) for c in self.components)

    def __str__(self) -> str:
        return self.canonical() or self.raw


@dataclass(frozen=True)
class Packaging:
    """A parsed CONDITIONNEMENT cell."""

    raw: str
    count: int | None = None
    container: str = ""
    volume: Component | None = None

    @property
    def parsed(self) -> bool:
        return self.count is not None or self.volume is not None


def parse_strength(raw: str | None) -> Strength:
    """Read a DOSAGE cell into its quantities.

    Components are separated by ``/``. A fragment that holds no number (the
    trailing ``ML`` of ``100MG/12,5MG/ML``) is kept in ``unparsed`` rather than
    discarded, so nothing from the source silently disappears.

    >>> parse_strength("325MG/37,5MG").canonical()
    '325mg+37.5mg'
    >>> parse_strength("0,03").parsed
    True
    >>> parse_strength("CF NOTICE").parsed
    False
    """
    text = (raw or "").strip()
    if not text:
        return Strength(raw="")

    components: list[Component] = []
    unparsed: list[str] = []

    for fragment in text.split("/"):
        fragment = fragment.strip()
        if not fragment:
            continue
        match = _COMPONENT_RE.match(fragment)
        if match:
            components.append(
                Component(
                    value=_to_float(match.group("value")),
                    unit=normalize_unit(match.group("unit")),
                )
            )
        else:
            unparsed.append(fragment)

    return Strength(raw=text, components=tuple(components), unparsed=tuple(unparsed))


def parse_packaging(raw: str | None) -> Packaging:
    """Read a CONDITIONNEMENT cell.

    ``B/16`` is sixteen units in the box. ``B/FL 15 ML`` is a 15 ml bottle and
    has no unit count at all — returning 15 there would be a lie, so ``count``
    stays None and the volume is recorded separately.

    >>> parse_packaging("B/16").count
    16
    >>> parse_packaging("B/FL 15 ML").count is None
    True
    """
    text = (raw or "").strip()
    if not text:
        return Packaging(raw="")

    count_match = _PACK_COUNT_RE.match(text)
    if count_match:
        return Packaging(raw=text, count=int(count_match.group("count")))

    # La forme la plus riche en premier : elle porte un compte ET une mesure.
    # Essayee avant les autres, sinon "B/05 AMP. DE 2ML" serait lu comme un
    # simple volume de 2 ml et les cinq ampoules disparaitraient.
    for pattern in (_PACK_COMPTE_ET_MESURE_RE, _PACK_VOLUME_RE, _PACK_MESURE_SEULE_RE):
        match = pattern.match(text)
        if not match:
            continue
        groupes = match.groupdict()
        compte = groupes.get("count")
        return Packaging(
            raw=text,
            count=int(compte) if compte else None,
            container=groupes["container"].upper(),
            volume=Component(
                value=_to_float(groupes["value"]),
                unit=normalize_unit(groupes["unit"]),
            ),
        )

    return Packaging(raw=text)
