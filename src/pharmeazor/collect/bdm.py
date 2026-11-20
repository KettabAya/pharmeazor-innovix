"""Lire les PDF de la Base de Données publique des Médicaments (France).

Ce que c'est
------------
3 664 PDF collectés par l'équipe sur la base publique française, rangés par
molécule. Quatre documents par médicament :

===============  =====  ===========================================
type              part   à qui il s'adresse
===============  =====  ===========================================
``rcp``          1 098   au professionnel de santé
``notice``       1 098   au patient
``fiche_info``   1 103   résumé de la fiche publique
``bon_usage``      365   recommandations de bon usage
===============  =====  ===========================================

985 médicaments distincts : le long nombre du nom de fichier est un
identifiant, partagé par les documents d'un même médicament.

Le rang d'autorité, et pourquoi il compte
-----------------------------------------
C'est une source **étrangère et institutionnelle** : rang 2
(:data:`Authority.INSTITUTIONAL`), au-dessous de la nomenclature algérienne
qui est au rang 3.

Le cahier des charges est net :

    « Une source étrangère sert de complément, jamais de substitut à la
    source algérienne. »

Concrètement, pour ce module :

* la **posologie**, les **contre-indications**, les **interactions** et les
  **effets indésirables** d'une molécule sont transposables, et c'est
  précisément ce que la nomenclature ne contient pas ;
* **le produit, non.** Un RCP français décrit un médicament enregistré en
  France : son dosage, son conditionnement et son titulaire peuvent différer
  de l'algérien. Rien ici ne doit servir à dire ce qui est enregistré en
  Algérie.

Chaque passage produit le rappelle dans son texte, pour qu'un lecteur qui ne
voit que l'extrait sache déjà d'où il vient.

Ce que ce module ne fait pas
----------------------------
Il n'invente pas de rubrique. Le découpage est confié à
:func:`pharmeazor.extract.sections.split_sections`, et un document dont
aucune rubrique n'est reconnue ressort tel quel, signalé, plutôt que
découpé au jugé.
"""

from __future__ import annotations

import datetime as _dt
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from ..schemas import Authority, Provenance

__all__ = [
    "BDM_SOURCE_ID",
    "BDM_URL",
    "DocumentBDM",
    "TYPES_DE_DOCUMENT",
    "lire_nom_de_fichier",
    "parcourir",
    "extraire_texte",
]

BDM_SOURCE_ID = "bdm_france"
BDM_URL = "https://base-donnees-publique.medicaments.gouv.fr/"

# Les quatre types, du plus utile au pharmacien au moins utile.
TYPES_DE_DOCUMENT: tuple[str, ...] = ("rcp", "bon_usage", "fiche_info", "notice")

# <molecule>_<type>_<identifiant>.pdf
_NOM = re.compile(
    r"^(?P<molecule>.+)_(?P<type>rcp|notice|fiche_info|bon_usage)_(?P<identifiant>\d+)$"
)


def _sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in decompose if not unicodedata.combining(c))


@dataclass
class DocumentBDM:
    """Un PDF de la base française, identifié par son nom de fichier."""

    chemin: Path
    molecule: str
    type_document: str
    identifiant: str
    texte: str = ""
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def molecule_normalisee(self) -> str:
        """Le nom de molécule en majuscules sans accents, pour comparer.

        Les dossiers portent ``paracétamol``, notre périmètre ``PARACETAMOL``.
        """
        return _sans_accents(self.molecule).upper().strip()

    @property
    def intitule(self) -> str:
        """Le nom complet du medicament, lu dans le document lui-meme.

        La deuxieme ligne utile d'un RCP porte le nom, le dosage et la forme :

            Derniere mise a jour le 03/11/2026
            ACIDE ACETYLSALICYLIQUE BIOGARAN 75 mg, comprime gastro-resistant

        C'est ce qu'il faut mettre en tete de chaque passage. Sans lui, un
        extrait de rubrique ne nomme PAS le medicament qu'il decrit : la
        recherche par mots-cles ne peut pas le retrouver, et une citation
        prise seule ne dit pas de quoi elle parle. Constate le 19/11/2026 --
        une question sur la posologie du paracetamol ramenait un passage de
        codeine, parce qu'aucun des deux ne portait son nom.

        Si la lecture echoue, on retombe sur le nom de dossier, qui est
        toujours la.
        """
        for ligne in (x.strip() for x in self.texte.splitlines()):
            if not ligne or ligne.lower().startswith("dernière mise à jour"):
                continue
            return ligne[:160]
        return self.molecule

    @property
    def pour_le_pharmacien(self) -> bool:
        """Le RCP s'adresse au professionnel ; la notice, au patient.

        Notre assistant répond à un pharmacien : les deux restent lisibles,
        mais le RCP prime quand les deux existent.
        """
        return self.type_document in {"rcp", "bon_usage"}

    def provenance(self) -> Provenance:
        """Rang 2 : institutionnelle, étrangère.

        La date de collecte est celle du fichier sur le disque. C'est une
        approximation assumée — l'archive ne porte pas la date de
        téléchargement — et elle est toujours postérieure à la collecte, donc
        elle ne fait jamais paraître une donnée plus fraîche qu'elle n'est.
        """
        horodatage = _dt.date.fromtimestamp(self.chemin.stat().st_mtime)
        return Provenance(
            source_id=BDM_SOURCE_ID,
            url=BDM_URL,
            authority=Authority.INSTITUTIONAL,
            collected_at=horodatage,
            language="fr",
            country="FR",
        )


def lire_nom_de_fichier(chemin: Path) -> DocumentBDM | None:
    """Découper ``paracétamol_rcp_61143618.pdf`` en ses trois parties.

    Rend ``None`` quand le nom ne suit pas le motif, plutôt que de deviner :
    un fichier qu'on ne sait pas nommer ne doit pas entrer dans le corpus
    sous une molécule approximative.

    >>> d = lire_nom_de_fichier(Path("x/paracétamol/paracétamol_rcp_612.pdf"))
    >>> d.molecule, d.type_document, d.identifiant
    ('paracétamol', 'rcp', '612')
    """
    correspondance = _NOM.match(chemin.stem)
    if correspondance is None:
        return None
    return DocumentBDM(
        chemin=chemin,
        molecule=correspondance.group("molecule"),
        type_document=correspondance.group("type"),
        identifiant=correspondance.group("identifiant"),
    )


def parcourir(racine: str | Path,
              molecules: tuple[str, ...] = (),
              types: tuple[str, ...] = ()) -> Iterator[DocumentBDM]:
    """Parcourir l'arborescence et rendre les documents retenus.

    Args:
        racine: le dossier qui contient un sous-dossier par molécule.
        molecules: ne garder que celles-ci (majuscules sans accents).
            Vide = toutes.
        types: ne garder que ces types de document. Vide = tous.
    """
    racine = Path(racine)
    for chemin in sorted(racine.glob("*/*.pdf")):
        document = lire_nom_de_fichier(chemin)
        if document is None:
            continue
        if types and document.type_document not in types:
            continue
        if molecules and not any(
            document.molecule_normalisee.startswith(m) or
            m.startswith(document.molecule_normalisee)
            for m in molecules
        ):
            continue
        yield document


def extraire_texte(document: DocumentBDM) -> DocumentBDM:
    """Remplir ``texte`` depuis le PDF.

    Vérifié sur un échantillon le 19/11/2026 : les documents portent du vrai
    texte, aucun n'est une page scannée. Aucune OCR n'est donc nécessaire —
    et c'est une bonne nouvelle, l'OCR introduit des erreurs qu'une base de
    sécurité médicamenteuse ne peut pas se permettre.

    Un document illisible ressort avec un texte vide plutôt qu'en levant une
    exception : un PDF abîmé sur 3 664 ne doit pas arrêter toute la chaîne.
    """
    import pymupdf

    try:
        with pymupdf.open(document.chemin) as pdf:
            document.texte = "\n".join(page.get_text() for page in pdf)
    except Exception:
        document.texte = ""
    return document
