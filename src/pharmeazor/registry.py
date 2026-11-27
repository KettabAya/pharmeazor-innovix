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


def resolve_drug(name: str) -> str | None:
    """Brand name or DCI -> drug_id.

    The name index holds every way a product is written: brand, DCI, and the
    spellings the registry itself uses.
    """
    cherche = (name or "").strip().lower()
    if not cherche:
        return None
    for ligne in _table("name_index"):
        if ligne["alias_normalized"].lower() == cherche:
            return ligne["drug_id"]
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
