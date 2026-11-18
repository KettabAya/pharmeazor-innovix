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

# "<valeur> (<equivalent>)" : 1% (10MG/ML), 400MG (684MG).
# La parenthese redit la dose autrement ; elle ne s'ajoute pas a la premiere.
_VALEUR_ET_EQUIVALENT = re.compile(
    r"^\s*(?P<valeur>[^(]+?)\s*\(\s*(?P<equivalent>[^)]+?)\s*\)\s*$"
)


# --- Les mots qu'on reconnait dans un conditionnement ----------------------
#
# Des listes, pas des expressions regulieres : on peut les lire, et en ajouter
# un mot ne demande pas de relire une regle.

# Contenants dont le nombre qui suit est un nombre d'UNITES.
# Mesure sur les 5 423 conditionnements d'aout 2026 : la seule forme "B/N"
# couvre 53,1 %. Avec les autres contenants, 56,1 %.
CONTENANTS_QUI_COMPTENT = ["B", "BTE", "BOITE", "PILULIER", "PLQ", "PLAQUETTE",
                           # Faute du registre, un produit : PILULIRER/30.
                           # Meme famille que le PILULIER/10 repere a la main
                           # en semaine 1, que les tests avaient laisse passer.
                           "PILULIRER"]

# Contenants dont le contenu se MESURE : un tube de 15 g n'est pas 15 unites.
CONTENANTS_QUI_MESURENT = ["FL", "FLACON", "FLACONS", "F", "T", "TUBE", "TUBES",
                           "AMP", "AMPOULE", "AMPOULES", "SACHET", "SACHETS",
                           "POT", "SERINGUE", "STICK", "STICKS",
                           "RECIPIENT", "RECIPIENTS UNIDOSES"]

# Mots toleres apres le nombre : "B/30 SACHETS" vaut bien 30.
MOTS_DENOMBRABLES = ["SACHET", "SACHETS", "COMPRIME", "COMPRIMES", "CP",
                     "GELULE", "GELULES", "CAPSULE", "CAPSULES",
                     "SUPPOSITOIRE", "SUPPOSITOIRES", "OVULE", "OVULES",
                     "AMPOULE", "AMPOULES", "AMP", "PILULE", "PILULES",
                     "STICK", "STICKS", "DOSE", "DOSES", "UNITE", "UNITES",
                     # "B/10 FL" : dix flacons, c'est bien un compte. Le cas 3
                     # passe avant et echoue faute de mesure apres "FL".
                     "FL", "FLACON", "FLACONS", "TUBE", "TUBES"]

# L'ordre compte : "MG" avant "G", sinon "500MG" se lirait "500M" + "G".
UNITES_DE_MESURE = ["ML", "MG", "KG", "L", "G"]

# Deux presentations dans une seule cellule. On refuse de choisir.
SEPARATEURS_DE_PRESENTATIONS = [" ET ", " - ", " OU ", "OU FL"]

# Ustensiles livres avec le medicament. Ils ne changent ni le compte ni la
# mesure : "FL/100ML +PIPETTE GRADUEE EN KG" reste un flacon de 100 ml.
#
# La queue n'est retiree que si elle ne porte AUCUN chiffre. Sinon il s'agit
# d'un second composant -- "B/06FL. DE PDRE + 06AMP. DE 2,5ML DE SOLVANT" est
# un necessaire poudre + solvant, et le lire comme un simple flacon ferait
# disparaitre le solvant.
USTENSILES = ["PIPETTE", "SERINGUE", "GOBELET", "GOBLET", "CUILLERE",
              "DOSEUR", "COMPTE-GOUTTES", "CANULE", "APPLICATEUR"]


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

    # "<valeur> (<equivalent>)" : le registre donne d'abord une concentration,
    # puis la meme chose dite autrement entre parentheses.
    #
    #     1% (10MG/ML)        une creme a 1 %, soit 10 mg par ml
    #     5% ( 5G/100 G )     5 %, soit 5 g pour 100 g
    #     400MG (684MG)       400 mg de base, pour 684 mg de sel
    #
    # Mesure du 17/11/2026, avant cette regle : 9 des 10 dosages illisibles
    # suivaient ce motif. La valeur retenue est celle de GAUCHE, qui est la
    # dose annoncee ; l'equivalent part dans `unparsed`, visible mais jamais
    # compte deux fois.
    entre_parentheses = _VALEUR_ET_EQUIVALENT.match(text)
    if entre_parentheses:
        text = entre_parentheses.group("valeur").strip()
        unparsed.append(entre_parentheses.group("equivalent").strip())

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


def _retirer_ustensile(texte: str) -> str:
    """Couper la queue qui ne decrit qu'un ustensile livre avec le produit.

    "FL/100ML +PIPETTE GRADUEE EN KG" devient "FL/100ML" : la pipette ne
    change ni le volume du flacon ni le nombre d'unites.

    La coupe n'a lieu que si la queue ne porte AUCUN chiffre. Sinon c'est un
    second composant, et le perdre serait grave :
    "B/06FL DE PDRE + 06AMP DE 2,5ML DE SOLVANT" est un necessaire poudre plus
    solvant, pas un flacon de poudre.
    """
    for marque in ("+", " AVEC "):
        if marque not in texte:
            continue
        tete, _, queue = texte.partition(marque)
        if any(c.isdigit() for c in queue):
            continue  # un second composant, pas un ustensile
        if any(u in queue for u in USTENSILES):
            return tete.strip()
    return texte


def _separer_nombre_et_mot(texte: str) -> tuple[int | None, str]:
    """'05 AMP' et '01FL' donnent tous deux (5, 'FL') ou (1, 'FL').

    Le ministere ecrit parfois le nombre colle au contenant. Separer sur les
    espaces seuls raterait "B/01FL DE 125ML" -- huit produits du registre.
    """
    texte = texte.strip()
    chiffres = ""
    for caractere in texte:
        if caractere.isdigit():
            chiffres += caractere
        else:
            break
    if not chiffres:
        return None, ""
    return int(chiffres), texte[len(chiffres):].strip()


def _lire_mesure(texte: str) -> Component | None:
    """'125 ML' -> 125 ml.  Rend None si ce n'est pas une mesure.

    Les unites sont essayees dans l'ordre de la liste, et "MG" y precede "G" :
    sinon "500MG" se lirait "500M" suivi de "G", et le nombre serait faux.
    """
    texte = texte.strip()
    for unite in UNITES_DE_MESURE:
        if texte.endswith(unite):
            nombre = texte[: -len(unite)].strip()
            try:
                return Component(value=_to_float(nombre), unit=normalize_unit(unite))
            except ValueError:
                return None
    return None


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

    propre = _retirer_ustensile(text.upper().replace(".", " "))

    # Deux presentations dans une seule cellule : on ne choisit pas.
    # "B/30 ET B/90" decrit deux tailles de boite ; en retenir une serait
    # inventer. C'est une decision, pas un echec.
    for separateur in SEPARATEURS_DE_PRESENTATIONS:
        if separateur in propre:
            return Packaging(raw=text)

    if "/" in propre:
        gauche, droite = propre.split("/", 1)
    elif " DE " in propre:
        gauche, droite = propre.split(" DE ", 1)
    else:
        return Packaging(raw=text)
    gauche, droite = gauche.strip(), droite.strip()
    mots = droite.split()

    # Cas 1 : le contenant est a gauche et son contenu se mesure. "FL/125 ML"
    if gauche in CONTENANTS_QUI_MESURENT:
        mesure = _lire_mesure(droite)
        return Packaging(raw=text, container=gauche, volume=mesure) if mesure \
            else Packaging(raw=text)

    # Pour tout le reste, il faut une boite a gauche.
    if gauche not in CONTENANTS_QUI_COMPTENT:
        return Packaging(raw=text)

    # Cas 2 : une boite de N contenants, d'une mesure chacun.
    # "B/05 AMP DE 2ML" porte DEUX informations. On l'examine en premier :
    # sinon le cas 3 y lirait un simple volume de 2 ml et les cinq ampoules
    # disparaitraient.
    if " DE " in droite:
        avant, apres = droite.split(" DE ", 1)
        nombre, contenant = _separer_nombre_et_mot(avant)
        if nombre is not None and contenant in CONTENANTS_QUI_MESURENT:
            mesure = _lire_mesure(apres)
            if mesure:
                return Packaging(raw=text, count=nombre,
                                 container=contenant, volume=mesure)

    # Cas 3 : une boite qui annonce son contenant puis sa mesure. "B/FL 15 ML"
    if mots and mots[0] in CONTENANTS_QUI_MESURENT:
        mesure = _lire_mesure(" ".join(mots[1:]))
        if mesure:
            return Packaging(raw=text, container=mots[0], volume=mesure)

    # Cas 4 : une boite de N unites. "B/16", "B/30 SACHETS"
    if mots and mots[0].isdigit():
        reste = mots[1:]
        if not reste or (len(reste) == 1 and reste[0] in MOTS_DENOMBRABLES):
            return Packaging(raw=text, count=int(mots[0]))
        # "B/30SACHETS" : le mot est colle au nombre.
        chiffres = ""
        for caractere in droite:
            if caractere.isdigit():
                chiffres += caractere
            else:
                break
        if chiffres and droite[len(chiffres):].strip() in MOTS_DENOMBRABLES:
            return Packaging(raw=text, count=int(chiffres))

    return Packaging(raw=text)
