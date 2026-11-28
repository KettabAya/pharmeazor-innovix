"""Read the week-1 tables. One door for everyone who needs them.

The tables are the output of the data work: a catalogue, a name index,
interactions, equivalence groups, disagreements. Anything that answers a
pharmacist's question starts here.

Nothing is computed here. We find rows and give them back as the CSV writes
them, so the reader can always check the source.
"""

from __future__ import annotations

import csv
from functools import cache
from pathlib import Path

__all__ = [
    "resolve_drug",
    "resolve_drug_ids",
    "resolve_dci",
    "get_drug",
    "interactions_of",
    "equivalents_of",
    "conflicts_for",
]

REFERENCE = Path(__file__).resolve().parents[2] / "data" / "reference"
SUFFIXE = "_40molecules"


@cache
def _table(nom: str) -> tuple[dict[str, str], ...]:
    """Read one CSV, once. The tables don't change while the app runs."""
    chemin = REFERENCE / f"{nom}{SUFFIXE}.csv"
    with open(chemin, encoding="utf-8", newline="") as fichier:
        return tuple(csv.DictReader(fichier))


#: Les alias qui nomment vraiment un produit, du plus précis au moins précis.
#: Un code de registre n'en est pas un : il désigne une forme, pas un produit.
_ORDRE_DES_ALIAS = ("brand", "inn", "registration", "code")


#: Un alias plus court ne distingue rien : il vient d'un code de registre dont
#: la normalisation n'a laissé qu'une lettre, et il désignerait des centaines
#: de produits. Le catalogue ne les écrit plus, mais une table déjà produite
#: peut encore en contenir, alors on les ignore aussi à la lecture.
LONGUEUR_ALIAS_MINIMALE = 3


def _lignes_pour(name: str) -> list[dict[str, str]]:
    """Les lignes du name_index qui portent ce nom, les plus précises d'abord."""
    cherche = (name or "").strip().lower()
    if len(cherche) < LONGUEUR_ALIAS_MINIMALE:
        return []
    trouvees = [
        ligne
        for ligne in _table("name_index")
        if ligne["alias_normalized"].lower() == cherche
        and len(ligne["alias_normalized"].strip()) >= LONGUEUR_ALIAS_MINIMALE
    ]

    def rang(ligne: dict[str, str]) -> int:
        kind = (ligne.get("kind") or "").lower()
        return _ORDRE_DES_ALIAS.index(kind) if kind in _ORDRE_DES_ALIAS else len(_ORDRE_DES_ALIAS)

    return sorted(trouvees, key=rang)


def resolve_drug_ids(name: str) -> list[str]:
    """Brand name or DCI -> every drug_id written that way.

    Un nom commercial désigne souvent plusieurs produits : DOLIPRANE est un
    comprimé, une suspension buvable, un suppositoire, chacun avec son
    identifiant. Rendre le premier venu revient à en choisir un au hasard, et
    tout ce qui filtre là-dessus écarte alors les bons passages. Les voici donc
    tous, sans ordre de préférence autre que la précision de l'alias.
    """
    vus: list[str] = []
    for ligne in _lignes_pour(name):
        if ligne["drug_id"] not in vus:
            vus.append(ligne["drug_id"])
    return vus


def resolve_drug(name: str) -> str | None:
    """Brand name or DCI -> one drug_id, the most precisely named.

    Gardée pour le code qui n'attend qu'un identifiant. Quand le nom en désigne
    plusieurs, c'est :func:`resolve_drug_ids` qu'il faut appeler : ici, le choix
    ne peut être que partiellement fondé.
    """
    ids = resolve_drug_ids(name)
    return ids[0] if ids else None


def resolve_dci(name: str) -> str | None:
    """Brand name or DCI -> the substance, which a brand never ambiguates.

    Un nom commercial peut couvrir dix présentations ; toutes partagent leur
    substance. C'est la seule identité qu'on puisse tirer d'un nom sans
    risquer de se tromper de produit — et la seule que portent les passages
    venus de la base française ou du registre.
    """
    for ligne in _lignes_pour(name):
        if ligne.get("inn"):
            return ligne["inn"]
    return None


def get_drug(drug_id: str) -> dict[str, str] | None:
    """One row of the catalogue, or None."""
    for ligne in _table("drugs"):
        if ligne["drug_id"] == drug_id:
            return dict(ligne)
    return None


def interactions_of(drug_id: str) -> list[dict[str, str]]:
    """Interactions where this drug's substance appears, on either side.

    A product is concerned twice: when the interaction is listed under its own
    DCI, and when another drug names that DCI as the target.
    """
    produit = get_drug(drug_id)
    if produit is None:
        return []
    inn = produit["inn"]
    return [
        dict(ligne)
        for ligne in _table("interactions")
        if ligne["inn"] == inn or ligne["substance_cible"] == inn
    ]


def equivalents_of(drug_id: str) -> list[dict[str, str]]:
    """The products of the same equivalence group, this one included.

    A group means same DCI, same strength, same galenic family. It does not
    mean interchangeable: that call belongs to the pharmacist.
    """
    lignes = _table("equivalents")
    groupe = next(
        (ligne["group_id"] for ligne in lignes if ligne["drug_id"] == drug_id),
        None,
    )
    if groupe is None:
        return []
    return [dict(ligne) for ligne in lignes if ligne["group_id"] == groupe]


def conflicts_for(drug_id: str) -> list[dict[str, str]]:
    """Every recorded disagreement about this product.

    Two kinds, both keyed on the registration number: between the two sources
    (`conflits`), and between two versions of the official registry
    (`desaccords_versions`). We add a `table` key so the caller knows which.
    """
    produit = get_drug(drug_id)
    if produit is None:
        return []
    numero = produit["registration_no"]

    trouves: list[dict[str, str]] = []
    for nom in ("conflits", "desaccords_versions"):
        for ligne in _table(nom):
            if ligne["n_enregistrement"] == numero:
                enrichi = dict(ligne)
                enrichi["table"] = nom
                trouves.append(enrichi)
    return trouves
