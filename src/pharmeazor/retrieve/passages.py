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
import re
from collections.abc import Iterator
from pathlib import Path

from pharmeazor.config import settings
from pharmeazor.schemas import Authority, Passage, Provenance

__all__ = [
    "MIPH_URL",
    "passages_produits",
    "passages_retraits",
    "passages_equivalents",
    "passages_interactions",
    "construire_corpus",
]

# Le ministere publie la nomenclature ici. Verifie le 15/11/2026 : l'ancienne
# adresse du registre, www.mip.gov.dz, ne resout pas -- c'est miph, avec un H.
MIPH_URL = "https://miph.gov.dz/"

# Un dosage ecrit en fraction nue, sans unite : « 0,001 » pour 0,1 %.
# La regle de lecture vit dans normalize.dosage ; ici on s en sert
# seulement pour expliquer la valeur au lecteur du passage.
_FRACTION_NUE = re.compile(r"^0[.,][0-9]+$")

_REFERENCE = settings.reference_dir


def _date_de_version(version: str) -> _dt.date:
    """``"2026-08"`` -> le 1er du mois.

    La nomenclature est publiee par version mensuelle, sans jour. On retient le
    premier du mois, et le champ ``source_version`` reste dans le texte du
    passage pour que le lecteur voie la version exacte.
    """
    annee, _, mois = version.partition("-")
    return _dt.date(int(annee), int(mois or 1), 1)


def _lire(nom: str, suffixe: str = "") -> list[dict[str, str]]:
    """Lire un livrable de data/reference/, dans la version demandee.

    Sans suffixe, ce sont les fichiers de la semaine 1 : 284 produits, trois
    molecules. Avec ``--suffixe _40molecules``, la version elargie : 914
    produits, 38 molecules.

    Les deux jeux coexistent exprès. Le rapport de la semaine 1 annonce des
    chiffres precis a l'enseignant ; les ecraser ferait mentir le rapport.
    """
    if suffixe:
        tronc = nom.removesuffix(".csv").removesuffix("_semaine1")
        nom = f"{tronc}{suffixe}.csv"
    chemin = _REFERENCE / nom
    if not chemin.exists():
        raise FileNotFoundError(
            f"{chemin} est absent. Lancez d'abord : python scripts/build_week1.py"
            + (f" --suffixe {suffixe}" if suffixe else "")
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


def passages_produits(lignes: list[dict[str, str]] | None = None,
                      suffixe: str = "") -> Iterator[Passage]:
    """Un passage par produit enregistré.

    Répond aux questions de niveau 1 : dosage, forme, conditionnement,
    laboratoire, DCI derrière un nom de marque, statut d'enregistrement.
    """
    for ligne in lignes if lignes is not None else _lire("drugs_semaine1.csv", suffixe):
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
            # « Son dosage est 0,001 » ne veut rien dire pour un pharmacien.
            # Le registre ecrit certaines concentrations en fraction nue ; on
            # le dit, et on donne l'equivalent en pourcentage, qui est la
            # facon dont le meme registre ecrit les autres produits.
            if _FRACTION_NUE.match(ligne["strength_raw"].strip()):
                pourcent = float(ligne["strength_raw"].strip().replace(",", ".")) * 100
                lisible = f"{pourcent:g}".replace(".", ",")
                corps.append(
                    "Le registre écrit ce dosage en fraction, sans unité. "
                    f"Lu comme un pourcentage, cela vaut {lisible} % — cette "
                    "conversion est notre lecture, elle n'est pas écrite dans "
                    "le registre."
                )
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
            # Le registre porte ici une lettre, F ou I, dont la legende n'est
            # publiee nulle part. Ecrire « Son statut est : F » laissait
            # croire au lecteur qu'il devait comprendre ce code. On dit donc
            # ce qu'on sait : le code, et qu'il n'est pas documente.
            corps.append(
                f"Le registre lui donne le code de statut « {ligne['status']} », "
                "dont la légende n'est publiée nulle part."
            )
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


def passages_retraits(lignes: list[dict[str, str]] | None = None,
                      suffixe: str = "") -> Iterator[Passage]:
    """Un passage par produit sorti du marche.

    Pourquoi ils sont dans le corpus alors qu'ils ne sont pas dans le catalogue
    --------------------------------------------------------------------------
    Un produit retire ne doit jamais etre propose comme equivalent : il n'est
    donc pas dans `drugs_*.csv`, et aucun groupe d'equivalents ne peut le faire
    remonter.

    Mais ne pas savoir qu'il a existe est un autre probleme. Sans ces passages,
    « c'est quoi, ASPIRINE PH8 ? » n'obtenait rien -- un silence qui se lit
    « je ne sais pas », alors que le registre dit « retire le 2011-05-08, par
    le MSPRH, pour interdiction de la substance ». Les deux reponses n'ont pas
    du tout le meme sens pour un pharmacien.

    Chaque passage commence donc par dire que le produit n'est plus
    enregistre. C'est la premiere chose a lire, avant le dosage et la forme.
    """
    lignes = lignes if lignes is not None else _lire("retraits_semaine1.csv", suffixe)
    # Le rang sert d'identifiant : deux produits peuvent partager un numero
    # d'enregistrement -- c'est un cas reel du registre, deja constate sur la
    # feuille principale -- et deux passages de meme identifiant fausseraient
    # la comparaison entre methodes de recherche.
    for rang, ligne in enumerate(lignes, 1):
        marque = ligne["brand_name"]
        retire = ligne["source_sheet"] == "retraits"

        tete = (f"{marque} N'EST PLUS un médicament enregistré en Algérie."
                if retire else
                f"{marque} n'est plus enregistré en Algérie : son "
                "enregistrement n'a pas été renouvelé.")
        corps = [tete]
        if ligne["withdrawal_date"]:
            corps.append(f"Il a été retiré le {ligne['withdrawal_date']}.")
        if ligne["withdrawal_reason"]:
            corps.append(f"Motif du retrait : {ligne['withdrawal_reason']}.")
        if ligne["inn"]:
            corps.append(f"Sa substance active (DCI) était {ligne['inn']}.")
        if ligne["form"]:
            corps.append(f"Il se présentait sous forme de {ligne['form']}.")
        if ligne["strength_raw"]:
            corps.append(f"Son dosage était {ligne['strength_raw']}.")
        if ligne["lab_name"]:
            corps.append(f"Il était produit par {ligne['lab_name']}.")
        if ligne["registration_no"]:
            corps.append(f"Son numéro d'enregistrement était {ligne['registration_no']}.")
        corps.append(
            "Ce produit ne doit pas être délivré et ne peut pas servir "
            "d'équivalent."
        )
        corps.append(
            f"Source : nomenclature nationale, version {ligne['source_version']}, "
            f"feuille {ligne['source_sheet']}."
        )

        yield Passage(
            passage_id=f"nom-retrait-{rang:04d}",
            doc_id=f"nomenclature-{ligne['source_version']}",
            text=_phrase(corps),
            provenance=_provenance_nomenclature(ligne["source_version"]),
            section="retrait",
        )


def passages_equivalents(
    lignes: list[dict[str, str]] | None = None,
    suffixe: str = "",
) -> Iterator[Passage]:
    """Un passage par groupe d'équivalents.

    Répond à la question du pharmacien en rupture de stock : « par quoi puis-je
    remplacer ce médicament ? » Le groupe réunit même substance, même dosage,
    même famille de forme.
    """
    lignes = lignes if lignes is not None else _lire("equivalents_semaine1.csv", suffixe)

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
        # L'avertissement ci-dessus est general. Quand on sait PRECISEMENT ce
        # qui differe dans le groupe, on le nomme : un pharmacien ne peut pas
        # arbitrer sur « peuvent differer », il arbitre sur « l'un est
        # gastro-resistant, l'autre non ».
        ecarts = tete.get("differences_dans_le_groupe", "").strip()
        if ecarts:
            corps.append(
                f"Attention, ce groupe n'est pas homogène sur : {ecarts}. "
                "La décision revient au pharmacien."
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
    suffixe: str = "",
) -> Iterator[Passage]:
    """Un passage par interaction médicamenteuse.

    L'autorité est celle que la semaine 1 a retenue : le contenu vient du
    thésaurus ANSM (rang 2), mais il nous parvient par un relais secondaire,
    donc l'autorité effective retombe au rang 1. Le passage le dit.
    """
    lignes = lignes if lignes is not None else _lire("interactions_semaine1.csv", suffixe)

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
        # « Medicament concerne : BIOFENAC » etait faux par omission.
        #
        # Une interaction concerne une SUBSTANCE, donc TOUS les produits qui
        # la contiennent. La colonne brand_name de la table ne nomme qu'un
        # produit : le premier rencontre dans l'export dzair. Mesure du
        # 19/11/2026 : les 16 interactions du diclofenac sodique citaient
        # BIOFENAC, alors que 36 marques du catalogue portent cette substance.
        #
        # Nommer une marque laissait donc entendre que les 35 autres ne sont
        # pas concernees. On nomme la substance, et on dit d'ou vient la fiche.
        corps.append(
            f"Cette interaction concerne la substance {ligne['inn']}, donc "
            "TOUS les médicaments qui la contiennent, quelle que soit leur "
            "marque."
        )
        if ligne["brand_name"]:
            corps.append(
                f"Fiche d'où l'information a été lue : {ligne['brand_name']}."
            )

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


def construire_corpus(suffixe: str = "") -> list[Passage]:
    """Tout le corpus de la semaine 1, prêt à être indexé.

    C'est le point d'entrée : ``BM25Index`` et le futur index vectoriel
    travaillent tous deux sur cette liste, ce qui rend la comparaison honnête —
    mêmes passages, mêmes identifiants, seule la méthode de recherche change.
    """
    corpus = [
        *passages_produits(suffixe=suffixe),
        *passages_retraits(suffixe=suffixe),
        *passages_equivalents(suffixe=suffixe),
        *passages_interactions(suffixe=suffixe),
    ]
    vus = {p.passage_id for p in corpus}
    if len(vus) != len(corpus):
        raise ValueError(
            "Deux passages portent le même identifiant : la comparaison entre "
            "méthodes de recherche serait faussée."
        )
    return corpus


def chemin_corpus(suffixe: str = "") -> Path:
    """Où le corpus est écrit par ``scripts/construire_corpus.py``.

    Chaque jeu a son fichier : sans suffixe ``corpus_semaine1.jsonl``,
    avec ``_40molecules`` le fichier ``corpus_40molecules.jsonl``. Les deux
    coexistent, comme les tables dont ils sont tires.
    """
    if suffixe:
        return settings.processed_dir / f"corpus{suffixe}.jsonl"
    return settings.processed_dir / "corpus_semaine1.jsonl"
