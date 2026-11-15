"""Transformer les données de la semaine 1 en passages interrogeables.

Pourquoi ce module existe
-------------------------
La semaine 2 demande de découper des documents, de les indexer et de comparer
deux méthodes de recherche. Le plan supposait que ces documents soient les RCP
et les notices collectés par l'équipe — or ils vivent dans ``data/raw/notices/``,
dossier ignoré par git : ils n'existent que sur la machine de la personne qui
les a téléchargés, et la collecte n'est pas terminée.

Mais un corpus est déjà là, versionné dans le dépôt, reproductible par
n'importe qui : les tables produites en semaine 1. 284 produits, 242 produits
regroupés en équivalents, 87 interactions avec leur niveau ANSM. Ce ne sont pas
des documents au sens de la notice, mais ce sont des **faits sourcés**, et une
question de pharmacien comme « quel dosage pour ce médicament ? » ou « peut-on
associer X et Y ? » y trouve sa réponse.

Ce module les rend interrogeables. Il débloque donc le découpage, l'indexation,
les embeddings et la comparaison BM25/vecteurs **sans attendre la fin de la
collecte**.

Ce que ce module ne fait pas
----------------------------
Il n'invente rien. Un champ vide ne produit pas de phrase : il est omis. Les
nombres sont recopiés **tels quels** depuis la table, jamais reformatés, pour
que ``answer.number_guard`` puisse les retrouver mot pour mot dans le passage
cité — et pour que ``Citation`` accepte la citation.

Il ne remplace pas non plus les RCP : la nomenclature dit ce qui est enregistré,
pas la posologie ni les contre-indications. Un passage produit ici porte
l'autorité ``NOMENCLATURE`` (rang 3), pas ``OFFICIAL`` (rang 4).
"""

from __future__ import annotations

import csv
import datetime as _dt
from collections.abc import Iterator
from pathlib import Path

from pharmeazor.config import settings
from pharmeazor.schemas import Authority, Passage, Provenance

__all__ = [
    "MIPH_URL",
    "passages_produits",
    "passages_equivalents",
    "passages_interactions",
    "construire_corpus",
]

# Le ministere publie la nomenclature ici. Verifie le 15/11/2026 : l'ancienne
# adresse du registre, www.mip.gov.dz, ne resout pas -- c'est miph, avec un H.
MIPH_URL = "https://miph.gov.dz/"

_REFERENCE = settings.reference_dir


def _date_de_version(version: str) -> _dt.date:
    """``"2026-08"`` -> le 1er du mois.

    La nomenclature est publiee par version mensuelle, sans jour. On retient le
    premier du mois, et le champ ``source_version`` reste dans le texte du
    passage pour que le lecteur voie la version exacte.
    """
    annee, _, mois = version.partition("-")
    return _dt.date(int(annee), int(mois or 1), 1)


def _lire(nom: str) -> list[dict[str, str]]:
    chemin = _REFERENCE / nom
    if not chemin.exists():
        raise FileNotFoundError(
            f"{chemin} est absent. Lancez d'abord : python scripts/build_week1.py"
        )
    with open(chemin, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _provenance_nomenclature(version: str) -> Provenance:
    return Provenance(
        source_id="nomenclature",
        url=MIPH_URL,
        authority=Authority.NOMENCLATURE,
        collected_at=_date_de_version(version),
    )


def _phrase(morceaux: list[str]) -> str:
    """Assembler en omettant les morceaux vides.

    Un champ absent ne devient jamais une phrase du type « dosage : inconnu ».
    Le silence est plus honnête que le remplissage.
    """
    return " ".join(m.strip() for m in morceaux if m and m.strip())


def passages_produits(lignes: list[dict[str, str]] | None = None) -> Iterator[Passage]:
    """Un passage par produit enregistré.

    Répond aux questions de niveau 1 : dosage, forme, conditionnement,
    laboratoire, DCI derrière un nom de marque, statut d'enregistrement.
    """
    for ligne in lignes if lignes is not None else _lire("drugs_semaine1.csv"):
        marque = ligne["brand_name"]
        dci = ligne["inn"]

        corps = [f"{marque} est un médicament enregistré en Algérie."]
        if dci:
            corps.append(f"Sa substance active (DCI) est {dci}.")
        if ligne["form"]:
            corps.append(f"Il se présente sous forme de {ligne['form']}.")
        # Les dosages et conditionnements sont recopies tels quels : le
        # number_guard doit pouvoir les retrouver mot pour mot.
        if ligne["strength_raw"]:
            corps.append(f"Son dosage est {ligne['strength_raw']}.")
        if ligne["packaging_raw"]:
            corps.append(f"Son conditionnement est {ligne['packaging_raw']}.")
        if ligne["list_class"]:
            corps.append(f"Il relève de la {ligne['list_class']}.")
        if ligne["lab_name"]:
            pays = f" ({ligne['lab_country']})" if ligne["lab_country"] else ""
            corps.append(f"Il est produit par {ligne['lab_name']}{pays}.")
        if ligne["registration_no"]:
            corps.append(f"Son numéro d'enregistrement est {ligne['registration_no']}.")
        if ligne["date_initial"]:
            corps.append(f"Il est enregistré depuis le {ligne['date_initial']}.")
        if ligne["status"]:
            corps.append(f"Son statut est : {ligne['status']}.")
        corps.append(
            f"Source : nomenclature nationale, version {ligne['source_version']}."
        )

        yield Passage(
            passage_id=f"nom-produit-{ligne['drug_id']}",
            doc_id=f"nomenclature-{ligne['source_version']}",
            text=_phrase(corps),
            provenance=_provenance_nomenclature(ligne["source_version"]),
            section="produit",
        )


def passages_equivalents(
    lignes: list[dict[str, str]] | None = None,
) -> Iterator[Passage]:
    """Un passage par groupe d'équivalents.

    Répond à la question du pharmacien en rupture de stock : « par quoi puis-je
    remplacer ce médicament ? » Le groupe réunit même substance, même dosage,
    même famille de forme.
    """
    lignes = lignes if lignes is not None else _lire("equivalents_semaine1.csv")

    groupes: dict[str, list[dict[str, str]]] = {}
    for ligne in lignes:
        groupes.setdefault(ligne["group_id"], []).append(ligne)

    for group_id, membres in groupes.items():
        tete = membres[0]
        noms = sorted({m["brand_name"] for m in membres if m["brand_name"]})
        if len(noms) < 2:
            # Un groupe d'un seul produit n'apprend rien : il n'y a pas
            # d'equivalent a proposer.
            continue

        corps = [
            f"{len(noms)} médicaments enregistrés en Algérie sont équivalents : "
            f"{', '.join(noms)}.",
            f"Ils partagent la même substance active, {tete['inn']}.",
        ]
        if tete["strength"]:
            corps.append(f"Ils ont le même dosage, {tete['strength']}.")
        if tete["form_family"]:
            corps.append(f"Ils appartiennent à la famille de formes {tete['form_family']}.")
        labos = sorted({m["lab_name"] for m in membres if m["lab_name"]})
        if labos:
            corps.append(f"Laboratoires concernés : {', '.join(labos)}.")
        corps.append(
            "Une équivalence de substance, de dosage et de forme ne vaut pas "
            "interchangeabilité clinique : excipients et biodisponibilité "
            "peuvent différer."
        )
        corps.append("Source : nomenclature nationale.")

        yield Passage(
            passage_id=f"nom-equiv-{group_id}",
            doc_id="nomenclature-equivalents",
            text=_phrase(corps),
            provenance=_provenance_nomenclature("2026-08"),
            section="equivalents",
        )


def passages_interactions(
    lignes: list[dict[str, str]] | None = None,
) -> Iterator[Passage]:
    """Un passage par interaction médicamenteuse.

    L'autorité est celle que la semaine 1 a retenue : le contenu vient du
    thésaurus ANSM (rang 2), mais il nous parvient par un relais secondaire,
    donc l'autorité effective retombe au rang 1. Le passage le dit.
    """
    lignes = lignes if lignes is not None else _lire("interactions_semaine1.csv")

    for i, ligne in enumerate(lignes):
        cible = ligne["substance_cible"]
        if not cible:
            continue

        corps = [
            f"Interaction médicamenteuse entre {ligne['inn']} et {cible}.",
        ]
        if ligne["niveau"]:
            corps.append(f"Niveau de l'interaction : {ligne['niveau']}.")
        if ligne["risques"]:
            corps.append(f"Risque : {ligne['risques']}")
        if ligne["conduite_a_tenir"]:
            corps.append(f"Conduite à tenir : {ligne['conduite_a_tenir']}")
        if ligne["brand_name"]:
            corps.append(f"Médicament concerné : {ligne['brand_name']}.")

        origine = ligne["source_origine"] or "inconnue"
        relais = ligne["source_relais"] or "inconnu"
        corps.append(
            f"Information issue de {origine}, obtenue par l'intermédiaire de "
            f"{relais}. Un relais pouvant introduire une erreur, cette "
            f"information est à confirmer dans le thésaurus de l'ANSM avant "
            f"toute décision."
        )

        yield Passage(
            passage_id=f"interaction-{i:04d}",
            doc_id="interactions-ansm-relayees",
            text=_phrase(corps),
            provenance=Provenance(
                source_id="dzair_pharma",
                url=ligne["url"] or "",
                # Relayee : min(origine, PROFESSIONAL), comme collect.dzair.
                authority=Authority.PROFESSIONAL,
                collected_at=_dt.date(2026, 11, 13),
            ),
            section="interactions",
        )


def construire_corpus() -> list[Passage]:
    """Tout le corpus de la semaine 1, prêt à être indexé.

    C'est le point d'entrée : ``BM25Index`` et le futur index vectoriel
    travaillent tous deux sur cette liste, ce qui rend la comparaison honnête —
    mêmes passages, mêmes identifiants, seule la méthode de recherche change.
    """
    corpus = [
        *passages_produits(),
        *passages_equivalents(),
        *passages_interactions(),
    ]
    vus = {p.passage_id for p in corpus}
    if len(vus) != len(corpus):
        raise ValueError(
            "Deux passages portent le même identifiant : la comparaison entre "
            "méthodes de recherche serait faussée."
        )
    return corpus


def chemin_corpus() -> Path:
    """Où le corpus est écrit par ``scripts/construire_corpus.py``."""
    return settings.processed_dir / "corpus_semaine1.jsonl"
