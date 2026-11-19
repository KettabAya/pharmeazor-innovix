"""Build the week-1 deliverables from the two sources.

Reads the official nomenclature workbook and the dzair-pharma exports, keeps the
three starter molecules, then produces:

* ``data/reference/drugs_semaine1.csv``        — the merged product table
* ``data/reference/name_index.csv``            — every written form -> a product
* ``data/reference/equivalents_semaine1.csv``  — interchangeable boxes
* ``data/reference/interactions_semaine1.csv`` — interactions with their level
* ``data/reference/conflits_semaine1.csv``     — where the two sources disagree

and prints a worked answer with its citations.

Usage::

    python scripts/build_week1.py
    python scripts/build_week1.py --question BRUFEN
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmeazor.collect.dzair import load_directory  # noqa: E402
from pharmeazor.collect.nomenclature import read_workbook  # noqa: E402
from pharmeazor.config import MOLECULES_PROJET  # noqa: E402
from pharmeazor.normalize.catalogue import Catalogue  # noqa: E402
from pharmeazor.normalize.substance import (  # noqa: E402
    concerne_molecule,
    normaliser_substance,
    parse_inn,
)
from pharmeazor.reconcile.crosscheck import compare_all  # noqa: E402

# The three starter molecules: one per therapeutic class, as the spec asks.
# Override on the command line with --inn.
TARGET_INN: tuple[str, ...] = ("PARACETAMOL", "AMOXICILLINE", "AMLODIPINE")

# A quelle classe appartient chaque substance. Ce qui n'est pas liste ressort
# « non_classe » : le programme ne devine jamais une classe therapeutique.
#
# Cette table etait restee a cinq entrees, ecrites pour les trois molecules de
# la semaine 1. Mesure du 19/11/2026 : 510 produits sur 914 (79 DCI) sortaient
# « non_classe » pour cette seule raison -- tous les antibiotiques sauf
# l'amoxicilline, tous les antihypertenseurs sauf l'amlodipine.
#
# Les classes sont volontairement plus fines qu'en semaine 1. Le paracetamol
# etait range avec les AINS ; c'est faux : il est antalgique et antipyretique,
# il n'est pas anti-inflammatoire. Le melanger aux AINS laisserait croire
# qu'il partage leurs contre-indications digestives et renales.
CLASS_OF: dict[str, str] = {
    # Antalgiques qui ne sont pas des AINS.
    "PARACETAMOL": "antalgique",
    "TRAMADOL": "antalgique",
    "NEFOPAM": "antalgique",
    "CODEINE": "antalgique",

    # Anti-inflammatoires non steroidiens, l'aspirine comprise.
    "IBUPROFENE": "ains",
    "DICLOFENAC": "ains",
    "KETOPROFENE": "ains",
    "NAPROXENE": "ains",
    "PIROXICAM": "ains",
    "MELOXICAM": "ains",
    "CELECOXIB": "ains",
    "ACIDE ACETYLSALICYLIQUE": "ains",
    "ACETYLSALICYLATE": "ains",

    "AMOXICILLINE": "antibiotique",
    "AZITHROMYCINE": "antibiotique",
    "CLARITHROMYCINE": "antibiotique",
    "CIPROFLOXACINE": "antibiotique",
    "LEVOFLOXACINE": "antibiotique",
    "DOXYCYCLINE": "antibiotique",
    "GENTAMICINE": "antibiotique",
    "CLINDAMYCINE": "antibiotique",
    "CEFTRIAXONE": "antibiotique",
    "CEFIXIME": "antibiotique",
    "CEFUROXIME": "antibiotique",
    "METRONIDAZOLE": "antibiotique",
    "SULFAMETHOXAZOLE": "antibiotique",
    "TRIMETHOPRIME": "antibiotique",

    # Antihypertenseurs : inhibiteur calcique, sartans et IEC.
    "AMLODIPINE": "antihypertenseur",
    "VALSARTAN": "antihypertenseur",
    "LOSARTAN": "antihypertenseur",
    "RAMIPRIL": "antihypertenseur",
    "PERINDOPRIL": "antihypertenseur",
    "ENALAPRIL": "antihypertenseur",

    # Diuretiques et betabloquants sont separes : ils abaissent la tension,
    # mais leurs effets indesirables et leurs surveillances n'ont rien a voir.
    "HYDROCHLOROTHIAZIDE": "diuretique",
    "INDAPAMIDE": "diuretique",
    "SPIRONOLACTONE": "diuretique",

    "ATENOLOL": "betabloquant",
    "BISOPROLOL": "betabloquant",
    "NEBIVOLOL": "betabloquant",
}

RAW_XLSX = ROOT / "data" / "raw" / "nomenclature"
RAW_JSON = ROOT / "data" / "raw" / "dzair"
REFERENCE = ROOT / "data" / "reference"

PRODUCTS = REFERENCE / "drugs_semaine1.csv"
NAME_INDEX = REFERENCE / "name_index.csv"
EQUIVALENTS = REFERENCE / "equivalents_semaine1.csv"
INTERACTIONS = REFERENCE / "interactions_semaine1.csv"
CONFLICTS = REFERENCE / "conflits_semaine1.csv"
RETRAITS = REFERENCE / "retraits_semaine1.csv"
NOMS_RETIRES = REFERENCE / "name_index_retraits.csv"


def rediriger_sorties(suffixe: str) -> None:
    """Ecrire les livrables sous un autre nom, au lieu des fichiers par defaut.

    Les livrables de la semaine 1 ont ete remis a l'enseignant avec des
    chiffres precis : 284 produits, 1 136 alias, 242 equivalents. Elargir le
    filtre des DCI sans rediriger les sorties les remplacerait en silence, et
    le rapport ne correspondrait plus aux fichiers.

    Avec ``--suffixe _40molecules``, la version elargie s'ecrit a cote :
    ``drugs_40molecules.csv``, ``name_index_40molecules.csv``, etc. Les deux
    jeux coexistent, et on peut les comparer.
    """
    global PRODUCTS, NAME_INDEX, EQUIVALENTS, INTERACTIONS, CONFLICTS, RETRAITS
    global NOMS_RETIRES
    if not suffixe:
        return
    # Le suffixe remplace "_semaine1" quand il est present, sinon il s'ajoute.
    def nommer(base: str) -> Path:
        tronc = base.removesuffix("_semaine1")
        return REFERENCE / f"{tronc}{suffixe}.csv"

    PRODUCTS = nommer("drugs_semaine1")
    NAME_INDEX = nommer("name_index")
    EQUIVALENTS = nommer("equivalents_semaine1")
    INTERACTIONS = nommer("interactions_semaine1")
    CONFLICTS = nommer("conflits_semaine1")
    RETRAITS = nommer("retraits_semaine1")
    NOMS_RETIRES = nommer("name_index_retraits")

# Les colonnes du livrable produit.
#
# `stability` a ete ajoutee le 19/11/2026. Le lecteur lisait deja la colonne
# DUREE DE STABILITE du classeur -- renseignee pour 857 produits sur 914 --
# mais elle ne figurait pas dans cette liste, donc elle etait lue puis
# abandonnee a la derniere ligne du traitement. C'est la duree de conservation
# annoncee a l'enregistrement : « 36 MOIS », « 24 MOIS ».
PRODUCT_FIELDS = [
    "drug_id", "therapeutic_class", "inn", "brand_name", "code",
    "registration_no", "form", "strength_raw", "packaging_raw", "list_class",
    "lab_name", "lab_country", "date_initial", "date_final", "type_code",
    "status", "stability", "source_version", "source_sheet",
]


def targeted(inn: str, targets: tuple[str, ...]) -> bool:
    """La DCI releve-t-elle d'une des molecules demandees ?

    La regle elle-meme vit dans `pharmeazor.normalize.substance`, pour que ce
    script, `comparer_versions.py` et les tests appliquent exactement la meme.
    Elle tient compte des ecritures sel-d'abord : « CHLORHYDRATE DE NEFOPAM »
    ne commence pas par « NEFOPAM », mais sa base si.
    """
    return concerne_molecule(inn, targets)


def normaliser_texte(valeur: str) -> str:
    """Espaces de bord retires, espaces internes ramenes a un seul.

    Ne touche ni a la casse ni au contenu : une marque reste telle qu'elle est
    ecrite dans la source, car c'est elle qu'on citera.
    """
    return " ".join(str(valeur or "").split())


def normaliser_liste(valeur: str) -> str:
    """Uniformiser la colonne LISTE.

    La source ecrit la meme categorie reglementaire de deux facons --
    « LISTE I » et « Liste I » -- ce qui produirait deux categories distinctes
    au moment de regrouper. La mise en majuscules uniformise la forme sans
    toucher au sens : les deux graphies designent la meme chose.

    Une case vide reste vide. Elle signifie « hors liste », c'est-a-dire vendu
    sans ordonnance, et la remplir inventerait une contrainte reglementaire.
    """
    return normaliser_texte(valeur).upper()


def therapeutic_class(inn: str) -> str:
    """La classe therapeutique, ou « non_classe » si on ne sait pas.

    Le test porte sur le texte ecrit puis sur la base lue par parse_inn, pour
    la meme raison que dans `targeted` : « CHLORHYDRATE DE NEFOPAM » ne
    commence pas par « NEFOPAM ».

    Dans une association, c'est la PREMIERE substance qui donne la classe,
    parce que c'est elle que le registre met en tete :
    « PARACETAMOL/CODEINE » est range en antalgique, « VALSARTAN/
    HYDROCHLOROTHIAZIDE » en antihypertenseur. La seconde substance reste
    lisible dans la colonne `inn`, qui n'est jamais reecrite.
    """
    upper = (inn or "").upper()
    for prefix, klass in CLASS_OF.items():
        if upper.startswith(prefix):
            return klass
    base = parse_inn(inn).base.upper()
    for prefix, klass in CLASS_OF.items():
        if base.startswith(prefix):
            return klass
    return "non_classe"


def classeur_le_plus_recent(bavard: bool = False) -> Path:
    """Le classeur a utiliser pour decrire l'etat ACTUEL du registre.

    Le dossier contient plusieurs versions datees. La table produit decrit ce
    qui est enregistre aujourd'hui, donc une seule version : la plus recente,
    que le tri par nom de fichier (nomenclature_AAAA-MM) place en dernier. Les
    versions anterieures servent a scripts/comparer_versions.py, qui mesure ce
    qui a change entre deux publications.
    """
    books = sorted(RAW_XLSX.glob("*.xlsx"))
    if not books:
        raise SystemExit(
            f"Aucun classeur dans {RAW_XLSX}. Copiez-y la nomenclature "
            "(voir docs/SEMAINE-1.md, etape 0.2)."
        )
    if bavard:
        print(f"  version retenue : {books[-1].stem.replace('nomenclature_', '')}"
              f"  (la plus recente des {len(books)} disponibles)")
    return books[-1]


def extract_nomenclature(targets: tuple[str, ...]) -> list[dict]:
    """Lire la feuille « Nomenclature » et garder les molecules demandees.

    Seule cette feuille alimente le catalogue : elle liste ce qui est
    enregistre aujourd'hui. Les feuilles « Retraits » et « Non Renouveles »
    sont lues a part par `extract_retraits`, pour qu'un produit retire ne
    puisse jamais etre propose comme equivalent.
    """
    rows: list[dict] = []
    for book in [classeur_le_plus_recent(bavard=True)]:
        for row in read_workbook(book, sheets={"nomenclature"}):
            if not targeted(row.inn, targets):
                continue
            rows.append({
                "drug_id": f"DZ-{len(rows) + 1:04d}",
                "therapeutic_class": therapeutic_class(row.inn),
                "inn": normaliser_texte(row.inn),
                "brand_name": normaliser_texte(row.brand_name),
                "code": row.code,
                "registration_no": row.registration_no,
                "form": normaliser_texte(row.form),
                "strength_raw": row.strength_raw,
                "packaging_raw": row.packaging_raw,
                "list_class": normaliser_liste(row.list_class),
                "lab_name": normaliser_texte(row.lab_name),
                "lab_country": normaliser_texte(row.lab_country),
                "date_initial": row.date_initial,
                "date_final": row.date_final,
                "type_code": row.type_code,
                "status": row.status,
                "stability": normaliser_texte(row.stability),
                "source_version": row.source_version,
                "source_sheet": row.source_sheet,
            })

    with open(PRODUCTS, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=PRODUCT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


RETRAIT_FIELDS = [
    "registration_no", "inn", "brand_name", "form", "strength_raw",
    "packaging_raw", "lab_name", "date_initial", "date_final",
    "withdrawal_date", "withdrawal_reason", "source_version", "source_sheet",
]


def extract_retraits(book: Path, targets: tuple[str, ...]) -> list[dict]:
    """Lire les feuilles « Retraits » et « Non Renouveles » du classeur.

    Pourquoi une table a part, et surtout pas dans le catalogue
    ------------------------------------------------------------
    Un produit retire ne doit JAMAIS ressortir comme equivalent : le proposer
    a un pharmacien serait l'envoyer chercher une boite qui n'existe plus, ou
    qui a ete interdite. Le catalogue reste donc ce qu'il est, la liste de ce
    qui est enregistre aujourd'hui.

    Mais ne pas savoir qu'un produit a existe est un autre probleme. Mesure du
    19/11/2026 sur le classeur d'aout : les deux feuilles contiennent 668 et
    302 produits de nos 38 molecules. Tant qu'elles n'etaient pas lues, la
    question « c'est quoi, ASPIRINE PH8 ? » n'avait aucune reponse -- alors
    que le fichier officiel dit, noir sur blanc :

        retire le 2011-05-08, RETRAIT PAR LE MSPRH POUR INTERDICTION...

    « Je ne sais pas » et « il a ete interdit en 2011 » ne sont pas la meme
    reponse. La premiere est un trou non documente, exactement ce que le reste
    du traitement s'interdit.

    La feuille « Retraits » n'a pas les memes colonnes que les deux autres :
    c'est le lecteur qui s'en charge, puisqu'il lit par titre et non par
    position.
    """
    rows: list[dict] = []
    for row in read_workbook(book, sheets={"retraits", "non_renouveles"}):
        if not targeted(row.inn, targets):
            continue
        rows.append({
            "registration_no": row.registration_no,
            "inn": normaliser_texte(row.inn),
            "brand_name": normaliser_texte(row.brand_name),
            "form": normaliser_texte(row.form),
            "strength_raw": row.strength_raw,
            "packaging_raw": row.packaging_raw,
            "lab_name": normaliser_texte(row.lab_name),
            "date_initial": row.date_initial,
            "date_final": row.date_final,
            "withdrawal_date": row.withdrawal_date,
            "withdrawal_reason": normaliser_texte(row.withdrawal_reason),
            "source_version": row.source_version,
            "source_sheet": row.source_sheet,
        })

    with open(RETRAITS, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=RETRAIT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def write_noms_retires(retires: list[dict]) -> int:
    """Un dictionnaire de noms pour les produits sortis du marche.

    Separe de `name_index`, pour deux raisons.

    D'abord la securite : un nom retire ne doit pas se melanger aux noms
    delivrables dans la meme table. Un programme qui lirait le dictionnaire
    sans regarder une colonne de plus proposerait un produit interdit.

    Ensuite la mesure : sans ce fichier, 544 des 626 marques retirees du
    perimetre n'etaient connues d'aucun dictionnaire. Un pharmacien qui tape
    ACTIGRIP n'obtenait rien -- pas « retire », rien du tout.
    """
    lignes: list[tuple[str, str, str, str, str]] = []
    for rang, r in enumerate(retires, 1):
        ident = f"DZ-R-{rang:04d}"
        for genre, valeur in (("brand", r["brand_name"]),
                              ("inn", r["inn"]),
                              ("registration", r["registration_no"])):
            if valeur:
                lignes.append((valeur, normaliser_substance(valeur), genre,
                               ident, r["source_sheet"]))

    with open(NOMS_RETIRES, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["alias", "alias_normalized", "kind", "retrait_id",
                         "source_sheet"])
        # Tri sur le tuple ENTIER, pas sur (kind, alias) : deux produits
        # peuvent porter la meme marque, et un tri a egalites laissait
        # l'ordre de `set` decider -- il change d'une execution a l'autre
        # parce que Python randomise le hachage des chaines. Le fichier
        # n'etait donc pas reproductible, ce qui ruine une empreinte SHA-256.
        writer.writerows(sorted(set(lignes)))
    return len(set(lignes))


def write_name_index(catalogue: Catalogue) -> int:
    aliases = catalogue.aliases()
    with open(NAME_INDEX, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["alias", "alias_normalized", "kind", "drug_id", "inn"])
        for a in sorted(aliases, key=lambda x: (x.kind, x.alias)):
            product = catalogue.get(a.drug_id)
            writer.writerow([a.alias, a.alias_normalized, a.kind, a.drug_id,
                             product.inn if product else ""])
    return len(aliases)


# Traits galeniques qui survivent au regroupement, et qui changent quelque
# chose pour le patient. La famille de forme les ignore : un comprime
# gastro-resistant et un comprime pellicule sont tous deux des COMPRIME.
_TRAITS_GALENIQUES: tuple[tuple[str, str], ...] = (
    ("libération prolongée", r"\bLP\b|PROLONG|RETARD|CHRONO|LIBERATION MODIFIEE"),
    ("gastro-résistant", r"GASTRO|ENTERIQUE"),
    ("effervescent", r"EFFERVESC|EFFERVESS"),
    ("orodispersible", r"ORODISPERS|LYOC|FONDANT"),
)


def differences_du_groupe(produits: list) -> list[str]:
    """Ce qui differe entre les membres d'un groupe d'equivalents.

    Un groupe reunit meme substance, meme dosage, meme famille de forme. Cela
    laisse passer des ecarts qui comptent pour le patient, et que la famille
    de forme ne voit pas. Mesure du 19/11/2026 sur les 153 groupes :

        4 groupes melangent un trait galenique
            EQ-0012  COMPRIME GASTRO-RESISTANT avec COMPRIME PELLICULE
            EQ-0035  COMPRIME EFFERVESCENT avec COMPRIME
            EQ-0098  COMPRIME ORODISPERSIBLE avec COMPRIME SECABLE
        12 groupes melangent le classement reglementaire
            LISTE I avec LISTE II, ou LISTE II avec une case vide

    Ces ecarts ne sont pas anodins. Un comprime gastro-resistant existe
    precisement pour ne pas liberer dans l'estomac -- pour un AINS, c'est
    tout l'interet. Un comprime effervescent apporte du sodium, ce qui
    compte chez un hypertendu. Et passer de « hors liste » a « LISTE I »
    change ce dont le patient a besoin : une ordonnance.

    Le groupe n'est PAS casse pour autant. Decider que deux presentations ne
    sont pas interchangeables est un jugement pharmaceutique ; le programme
    se contente de rendre l'ecart visible, comme il le fait deja pour la
    forme saline avec `sel_produit`.
    """
    ecarts: list[str] = []
    formes = [str(getattr(p, "form", "") or "").upper() for p in produits]
    for libelle, motif in _TRAITS_GALENIQUES:
        porte = [bool(re.search(motif, f)) for f in formes]
        if any(porte) and not all(porte):
            ecarts.append(libelle)
    classements = {str(getattr(p, "list_class", "") or "").strip() for p in produits}
    if len(classements) > 1:
        lisibles = ", ".join(sorted(c or "hors liste" for c in classements))
        ecarts.append(f"classement réglementaire ({lisibles})")
    return ecarts


def write_equivalents(catalogue: Catalogue) -> int:
    """Ecrire les groupes d'equivalents, chaque produit avec SA propre DCI.

    La colonne `inn` est celle du GROUPE : c'est la DCI du premier produit
    rencontre, et elle sert d'etiquette. Elle ne decrit pas forcement chaque
    membre, parce que le regroupement se fait sur la substance de base et
    laisse de cote la forme saline.

    Exemple constate le 17/11/2026 sur le groupe « diclofenac 50 mg
    comprime » : six produits sont du diclofenac sodique, trois du
    potassique -- RAPIDUS, BIOFENAC FAST, VOTREX RAPID, dont les noms
    annoncent eux-memes l'absorption plus rapide du sel de potassium. Les
    neuf lignes portaient pourtant « DICLOFENAC SODIQUE ».

    La colonne `inn_produit` porte donc la DCI exacte de chaque ligne, et
    `sel_produit` la forme saline lue par parse_inn. Un pharmacien voit ainsi
    ce qu'il delivre vraiment, et peut ecarter lui-meme un sel qui ne
    convient pas. Le regroupement, lui, n'est pas modifie : decider que deux
    sels ne sont pas interchangeables est un jugement pharmaceutique, pas une
    decision de programme.
    """
    groups = [g for g in catalogue.groups() if g.size > 1]
    with open(EQUIVALENTS, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "group_id", "inn", "strength", "form_family", "group_size",
            "differences_dans_le_groupe",
            "drug_id", "brand_name", "inn_produit", "sel_produit", "form",
            "packaging", "lab_name", "registration_no", "status",
        ])
        for i, group in enumerate(groups, 1):
            ecarts = " ; ".join(differences_du_groupe(group.products))
            for p in group.products:
                writer.writerow([
                    f"EQ-{i:04d}", group.inn, group.strength, group.form_family,
                    group.size, ecarts, p.drug_id, p.brand_name,
                    p.inn, p.substance.sel, p.form,
                    p.packaging.raw, p.lab_name, p.registration_no, p.status,
                ])
    return len(groups)


def write_interactions(dzair_products: list) -> tuple[int, dict[str, int]]:
    """Export every interaction, with its level and both sources."""
    levels: dict[str, int] = {}
    seen: set[tuple] = set()
    written = 0

    with open(INTERACTIONS, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "inn", "brand_name", "registration_no", "substance_cible",
            "type_cible", "niveau", "niveau_reconnu", "risques",
            "conduite_a_tenir", "source_origine", "source_relais",
            "autorite_effective", "url",
        ])
        for product in dzair_products:
            for item in product.interactions:
                key = (product.inn.upper(), item.substance.upper(), item.level_label)
                if key in seen:
                    continue
                seen.add(key)
                levels[item.level_fr] = levels.get(item.level_fr, 0) + 1
                writer.writerow([
                    product.inn, product.brand_name, product.registration_no,
                    item.substance, item.target_kind, item.level_fr,
                    "oui" if item.recognised else "non",
                    item.risks, item.what_to_do,
                    item.origin_source or "(non precisee)", "dzair_pharma",
                    item.effective_authority().label_fr, product.url,
                ])
                written += 1
    return written, levels


def _sans_ponctuation(valeur: str) -> str:
    """Un numero d'enregistrement, reduit a ses lettres et ses chiffres.

    Le ministere ecrit « 178/04 B 004/99 », dzair-pharma « 178 04 B 004 99 ».
    C'est le meme produit.
    """
    return re.sub(r"[^0-9A-Z]", "", str(valeur or "").upper())


def conflits_de_retrait(report, retires: list[dict]) -> list[list[str]]:
    """Les produits que dzair publie alors que le ministere les a retires.

    Constate le 19/11/2026 : les CINQ produits que la reconciliation listait
    comme « seulement chez dzair-pharma » -- sans jamais dire pourquoi --
    figurent tous dans la feuille « Retraits » du classeur officiel.

        BIDICLO LP   retire le 2021-08-25
        ALMIRAL      retire le 2011-05-08
        ALMIRAL      retire le 2007-06-12   (deux presentations)
        BIOFENAC     retire le 2015-07-09

    Dix-neuf ans pour le plus ancien. Ce n'est donc pas une lacune de notre
    appariement : c'est un VRAI desaccord entre les deux sources, et le plus
    grave qu'on puisse avoir -- une source secondaire qui presente comme
    disponible un medicament que l'autorite a retire du marche.

    Il fallait lire les feuilles de retraits pour pouvoir le dire. Tant
    qu'elles n'etaient pas lues, ces cinq lignes restaient un trou inexplique
    dans le rapport de reconciliation.
    """
    index = {_sans_ponctuation(r["registration_no"]): r for r in retires}
    lignes: list[list[str]] = []
    for numero in report.secondary_only:
        retire = index.get(_sans_ponctuation(numero))
        if retire is None:
            continue
        quand = retire["withdrawal_date"] or "date non precisee"
        motif = retire["withdrawal_reason"] or "motif non precise"
        lignes.append([
            numero,
            "statut d'enregistrement",
            f"sorti du marche ({retire['source_sheet']}), {quand} : {motif}",
            "publie comme enregistre",
            "nomenclature",
            "dzair_pharma",
            retire["source_version"],
            "export dzair",
            f"sorti du marche ({retire['source_sheet']}), {quand}",
            "La nomenclature nationale fait foi sur ce qui est enregistre en "
            "Algerie. Un produit absent de sa feuille courante et present dans "
            "ses feuilles de retraits n'est plus delivrable, quelle que soit la "
            "source qui continue de l'afficher.",
        ])
    return lignes


def write_conflicts(report, conflits_retrait: list[list[str]] | None = None) -> int:
    lignes_retrait = conflits_retrait or []
    with open(CONFLICTS, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "n_enregistrement", "champ", "valeur_officielle", "valeur_secondaire",
            "source_officielle", "source_secondaire", "collecte_officielle",
            "collecte_secondaire", "valeur_retenue", "justification",
        ])
        for d in report.disagreements:
            writer.writerow([
                d.registration_no, d.field_name, d.official_value,
                d.secondary_value, d.official_source, d.secondary_source,
                d.official_collected, d.secondary_collected, d.retained,
                d.reason_fr,
            ])
        writer.writerows(lignes_retrait)
    return len(report.disagreements) + len(lignes_retrait)


def show_answer(catalogue: Catalogue, name: str) -> None:
    answer = catalogue.equivalents_of(name)
    print("\n" + "=" * 74)
    print(f"QUESTION : « {name} est en rupture, quels équivalents enregistrés ? »")
    print("=" * 74)
    if answer["refused"]:
        print(f"\nRÉPONSE   : {answer['short']}")
        print(f"LIMITES   : {answer['limits']}")
        print("\n(Refus assumé : le système ne devine pas.)")
        return
    print(f"\nRÉPONSE   : {answer['short']}")
    print(f"\nEXPLICATION : {answer['explanation']}")
    print(f"\nSOURCES CITÉES ({len(answer['citations'])}) :")
    print(f"  {answer['citations'][0]['source']}")
    for c in answer["citations"][:8]:
        print(f"    [{c['registration_no']}] {c['quote']}")
    if len(answer["citations"]) > 8:
        print(f"    … et {len(answer['citations']) - 8} autres")
    print(f"\nLIMITES   : {answer['limits']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Livrables de la semaine 1.")
    parser.add_argument("--question", help="Nom de marque pour l'exemple travaillé.")
    parser.add_argument(
        "--inn", nargs="+", default=list(TARGET_INN),
        help="DCI à retenir (par défaut : une par classe thérapeutique).",
    )
    parser.add_argument(
        "--projet", action="store_true",
        help="Prendre les 38 molécules du projet et écrire sous le suffixe "
             "_40molecules. Raccourci de --inn <38 noms> --suffixe _40molecules.",
    )
    parser.add_argument(
        "--suffixe", default="",
        help="Écrire les livrables sous ce suffixe au lieu d'écraser ceux de "
             "la semaine 1. Exemple : --suffixe _40molecules",
    )
    args = parser.parse_args()
    # --projet évite de recopier 38 noms à la main : une faute de frappe y
    # perdait une molécule sans que rien ne le signale.
    if args.projet:
        args.inn = list(MOLECULES_PROJET)
        args.suffixe = args.suffixe or "_40molecules"
    rediriger_sorties(args.suffixe)
    targets = tuple(x.upper() for x in args.inn)

    print(f"Molécules retenues : {', '.join(targets)}\n")

    rows = extract_nomenclature(targets)
    print(f"[1] Nomenclature officielle : {len(rows)} produits -> {PRODUCTS.name}")
    # Le decompte affiche emploie `targeted`, la meme regle que le filtre.
    # Avec un simple startswith il annoncait NEFOPAM 0 alors que le produit
    # etait bien dans le fichier, et la somme des lignes affichees faisait
    # 911 pour un fichier de 914.
    # Deux colonnes, parce qu'un simple total se lit de travers : le
    # trimethoprime et l'hydrochlorothiazide ne sont JAMAIS la substance de
    # tete, ils n'existent dans le registre qu'en association
    # (SULFAMETHOXAZOLE/TRIMETHOPRIME, VALSARTAN/HYDROCHLOROTHIAZIDE).
    # Afficher « 0 » tout court laisserait croire a une molecule manquante.
    for inn in targets:
        n = sum(1 for r in rows if targeted(r["inn"], (inn,)))
        assoc = sum(1 for r in rows
                    if not targeted(r["inn"], (inn,))
                    and any(s.upper().startswith(inn)
                            for s in parse_inn(r["inn"]).toutes_substances))
        klass = therapeutic_class(inn)
        en_plus = f" + {assoc:>3} en association" if assoc else ""
        print(f"      {inn:<24} {n:>4}   ({klass}){en_plus}")
    compte = sum(1 for r in rows if any(targeted(r["inn"], (t,)) for t in targets))
    if compte != len(rows):
        print(f"      ATTENTION — {len(rows) - compte} ligne(s) du fichier ne "
              "sont comptees sous aucune molecule.")

    retires = extract_retraits(classeur_le_plus_recent(), targets)
    par_feuille: dict[str, int] = {}
    for r in retires:
        par_feuille[r["source_sheet"]] = par_feuille.get(r["source_sheet"], 0) + 1
    print("")
    print(f"[1b] Produits sortis du marché : {len(retires)} -> {RETRAITS.name}")
    for feuille, n in sorted(par_feuille.items()):
        print(f"      {feuille:<16} {n:>4}")
    dates = sum(1 for r in retires if r["withdrawal_date"])
    motifs = sum(1 for r in retires if r["withdrawal_reason"])
    print(f"      dont {dates} avec une date de retrait et {motifs} avec un motif")
    print("      Ils ne sont PAS dans le catalogue : un produit retiré ne doit")
    print("      jamais être proposé comme équivalent. Ils servent à répondre")
    print("      « il a été retiré le … » au lieu de « je ne sais pas ».")
    n_noms = write_noms_retires(retires)
    print(f"      {n_noms} noms retirés indexés -> {NOMS_RETIRES.name}")

    dzair = load_directory(RAW_JSON, only_inn=set(targets))
    covered = {inn for inn in targets
               if any(targeted(p.inn, (inn,)) for p in dzair)}
    missing = [inn for inn in targets if inn not in covered]
    n_inter = sum(len(p.interactions) for p in dzair)
    n_rcp = sum(1 for p in dzair if p.has_official_leaflet)
    print(f"\n[2] dzair-pharma (secondaire) : {len(dzair)} produits, "
          f"{n_inter} interactions, {n_rcp} lien(s) RCP officiel")
    if missing:
        print(f"      ATTENTION — aucune donnée dzair pour : {', '.join(missing)}")
        print("      Ces molécules n'ont qu'une seule source : pas d'interactions,")
        print("      pas de RCP officiel, et rien à réconcilier.")

    catalogue = Catalogue.from_csv(PRODUCTS)
    unparsed = [p for p in catalogue.products if not p.strength.parsed]
    print(f"\n[3] Dosages lus : {len(catalogue.products) - len(unparsed)}"
          f"/{len(catalogue.products)}")
    if unparsed:
        print(f"      non lus : {[p.strength.raw for p in unparsed][:6]}")

    n_aliases = write_name_index(catalogue)
    print(f"[4] Dictionnaire des noms : {n_aliases} entrées -> {NAME_INDEX.name}")

    n_groups = write_equivalents(catalogue)
    grouped = sum(g.size for g in catalogue.groups() if g.size > 1)
    print(f"[5] Équivalents : {n_groups} groupes, {grouped} produits -> {EQUIVALENTS.name}")

    n_written, levels = write_interactions(dzair)
    print(f"[6] Interactions : {n_written} uniques -> {INTERACTIONS.name}")
    for level, count in sorted(levels.items(), key=lambda kv: -kv[1]):
        print(f"      {count:>5}  {level}")

    report = compare_all(catalogue.products, dzair)
    retires_dzair = conflits_de_retrait(report, retires)
    n_conflicts = write_conflicts(report, retires_dzair)
    print("\n[7] Réconciliation des deux sources")
    print(f"      produits présents dans les deux : {len(report.pairs)}")
    print(f"      désaccords détectés             : {n_conflicts} -> {CONFLICTS.name}")
    print(f"      taux d'accord sur les champs    : {report.agreement_rate:.1%}")
    if report.by_field():
        print("      par champ :")
        for field_name, count in report.by_field().items():
            print(f"        {count:>4}  {field_name}")
    print(f"      seulement dans la nomenclature  : {len(report.official_only)}")
    print(f"      seulement chez dzair-pharma     : {len(report.secondary_only)}")
    if retires_dzair:
        print(f"        dont {len(retires_dzair)} que le ministère a RETIRÉS du marché")
        print("        et que dzair-pharma publie toujours comme enregistrés :")
        for ligne in retires_dzair:
            print(f"          {ligne[0]:<22} {ligne[2][:62]}")
        print("        C'est le désaccord le plus grave possible entre deux")
        print("        sources : l'une présente comme disponible ce que")
        print("        l'autorité a retiré. La nomenclature fait foi.")
    inexpliques = len(report.secondary_only) - len(retires_dzair)
    if inexpliques:
        print(f"        {inexpliques} reste(nt) sans explication.")

    demo = args.question
    if not demo:
        for group in catalogue.groups():
            for product in group.products:
                if not catalogue.equivalents_of(product.brand_name)["refused"]:
                    demo = product.brand_name
                    break
            if demo:
                break
    if demo:
        show_answer(catalogue, demo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
