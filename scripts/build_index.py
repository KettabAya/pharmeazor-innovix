"""Transformer les PDF de la base française en passages interrogeables.

Ce script était un squelette qui se terminait par ``NotImplementedError``.
Il est écrit le 19/11/2026, quand les 3 664 PDF collectés par l'équipe ont
enfin été versés dans ``data/raw/bdm/``.

Ce qu'il fait, dans l'ordre
---------------------------
1. parcourir l'arborescence et ne garder que les documents utiles ;
2. en extraire le texte (aucune OCR : les PDF portent du vrai texte) ;
3. les découper en rubriques avec ``extract.sections`` ;
4. couper chaque rubrique en passages de taille raisonnable ;
5. écrire ``data/processed/passages_bdm.jsonl`` et un récapitulatif.

Pourquoi seulement les RCP et le bon usage
------------------------------------------
Quatre types de documents existent. La notice s'adresse au **patient**, la
fiche d'information est un résumé public. Notre assistant répond à un
**pharmacien** : le RCP est le document qui lui parle, et le bon usage
complète. Les deux autres restent sur le disque, lisibles, et le choix est
réversible d'une option.

Le rang d'autorité, qui décide de tout
--------------------------------------
Ces documents sont **français** : rang 2, au-dessous de la nomenclature
algérienne. La posologie et les contre-indications d'une molécule sont
transposables ; **le produit, non**. Chaque passage le dit dans son texte.

Usage::

    python scripts/build_index.py
    python scripts/build_index.py --types rcp notice
    python scripts/build_index.py --limite 50
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmeazor.collect.bdm import (  # noqa: E402
    TYPES_DE_DOCUMENT,
    extraire_texte,
    parcourir,
)
from pharmeazor.config import MOLECULES_PROJET, settings  # noqa: E402
from pharmeazor.extract.sections import split_sections  # noqa: E402
from pharmeazor.schemas import Passage  # noqa: E402

RACINE_PDF = ROOT / "data" / "raw" / "bdm" / "row-data" / "pdf" / "bdm_pdf"
SORTIE = ROOT / "data" / "processed" / "passages_bdm.jsonl"
RECAP = ROOT / "data" / "reference" / "documents_bdm.csv"

# Les rubriques qui intéressent un pharmacien, dans l'ordre où il les lit.
RUBRIQUES_UTILES = ("indications", "posologie", "contre_indications",
                    "interactions", "effets_indesirables")

# La phrase qui accompagne CHAQUE passage.
#
# Elle n'est pas decorative. Un passage extrait voyage seul : il peut etre
# cite sans son contexte, et rien dans son texte ne dirait alors qu'il decrit
# un medicament francais. La regle du projet est qu'une source etrangere
# complete, jamais ne remplace -- il faut donc que la phrase parte AVEC le
# passage.
AVERTISSEMENT = (
    "Source française (base de données publique des médicaments), autorité "
    "institutionnelle étrangère : elle complète la nomenclature algérienne, "
    "elle ne la remplace pas. Le produit décrit est enregistré en France ; "
    "son dosage, son conditionnement et son titulaire peuvent différer de "
    "ceux du produit algérien du même nom."
)


def decouper(texte: str, taille: int, recouvrement: int) -> list[str]:
    """Couper un texte long en morceaux qui se chevauchent.

    Le recouvrement evite de trancher une phrase en deux sans que ni l'un ni
    l'autre morceau ne la contienne entiere -- ce qui rendrait la citation
    impossible a verifier.
    """
    mots = texte.split()
    if not mots:
        return []
    if sum(len(m) + 1 for m in mots) - 1 <= taille:
        return [" ".join(mots)]

    # On travaille par MOTS, pas par caracteres.
    #
    # Une premiere version coupait sur les caracteres en reculant jusqu'a un
    # espace. Le debut du morceau suivant, lui, retombait au milieu d'un mot :
    # « mot285 » devenait « t285 ». Mes propres tests l'ont attrape -- c'est
    # exactement ce qu'un test doit faire.
    morceaux: list[str] = []
    debut = 0
    while debut < len(mots):
        longueur, fin = 0, debut
        while fin < len(mots) and (longueur + len(mots[fin]) + 1) <= taille + 1:
            longueur += len(mots[fin]) + 1
            fin += 1
        fin = max(fin, debut + 1)          # toujours avancer d'au moins un mot
        morceaux.append(" ".join(mots[debut:fin]))
        if fin >= len(mots):
            break
        # Reculer de `recouvrement` caracteres, en comptant des mots entiers.
        reculee, k = 0, fin
        while k > debut + 1 and reculee < recouvrement:
            k -= 1
            reculee += len(mots[k]) + 1
        debut = k
    return morceaux


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--types", nargs="+", default=["rcp", "bon_usage"],
        choices=list(TYPES_DE_DOCUMENT),
        help="Types de documents à verser (défaut : rcp et bon_usage).",
    )
    parser.add_argument(
        "--toutes-molecules", action="store_true",
        help="Ne pas filtrer sur les 40 molécules du projet.",
    )
    parser.add_argument("--limite", type=int, default=0,
                        help="S'arrêter après N documents (pour essayer vite).")
    args = parser.parse_args()

    if not RACINE_PDF.exists():
        print(f"{RACINE_PDF} est absent.")
        print("Extrayez-y l'archive des PDF collectés par l'équipe.")
        return 1

    molecules = () if args.toutes_molecules else MOLECULES_PROJET
    documents = list(parcourir(RACINE_PDF, molecules=molecules,
                               types=tuple(args.types)))
    if args.limite:
        documents = documents[: args.limite]

    print(f"  {len(documents)} document(s) à traiter")
    print(f"  types retenus : {', '.join(args.types)}")
    if molecules:
        print(f"  filtrés sur les {len(molecules)} termes du périmètre")
    print()

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    par_type: Counter = Counter()
    par_rubrique: Counter = Counter()
    sans_texte = sans_rubrique = 0
    lignes_recap: list[list[str]] = []
    passages_ecrits = 0
    debut = time.time()

    with open(SORTIE, "w", encoding="utf-8") as sortie:
        for rang, document in enumerate(documents, 1):
            extraire_texte(document)
            if not document.texte.strip():
                sans_texte += 1
                continue

            decoupe = split_sections(document.texte)
            rubriques = {nom: texte for nom, texte in decoupe.sections.items()
                         if nom in RUBRIQUES_UTILES and texte.strip()}
            if not rubriques:
                sans_rubrique += 1

            provenance = document.provenance()
            par_type[document.type_document] += 1
            n_passages = 0

            for rubrique, contenu in rubriques.items():
                par_rubrique[rubrique] += 1
                for i, morceau in enumerate(
                    decouper(contenu, settings.passage_chars,
                             settings.passage_overlap)
                ):
                    passage = Passage(
                        passage_id=(f"bdm-{document.identifiant}-"
                                    f"{document.type_document}-{rubrique}-{i:02d}"),
                        doc_id=f"bdm-{document.identifiant}",
                        # L'en-tete nomme le medicament ET la rubrique. Un
                        # passage voyage seul : sans ca, il ne dit pas de
                        # quoi il parle, et la recherche ne le trouve pas.
                        text=(f"{document.intitule} — {rubrique.replace('_', ' ')}. "
                              f"{morceau} {AVERTISSEMENT}"),
                        provenance=provenance,
                        section=rubrique,
                    )
                    sortie.write(json.dumps({
                        "passage_id": passage.passage_id,
                        "doc_id": passage.doc_id,
                        "section": passage.section,
                        "molecule": document.molecule_normalisee,
                        "type_document": document.type_document,
                        "text": passage.text,
                        "source_id": provenance.source_id,
                        "autorite": int(provenance.authority),
                        "pays": "FR",
                        "url": provenance.url,
                    }, ensure_ascii=False) + "\n")
                    n_passages += 1
                    passages_ecrits += 1

            lignes_recap.append([
                document.identifiant, document.molecule_normalisee,
                document.type_document, str(len(document.texte)),
                f"{decoupe.coverage:.2f}", ";".join(sorted(rubriques)),
                str(n_passages), document.chemin.name,
            ])

            if rang % 200 == 0:
                print(f"    {rang}/{len(documents)} documents, "
                      f"{passages_ecrits} passages...", flush=True)

    with open(RECAP, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["identifiant", "molecule", "type_document",
                         "caracteres", "couverture_rubriques", "rubriques",
                         "passages", "fichier"])
        writer.writerows(sorted(lignes_recap))

    duree = time.time() - debut
    print()
    print(f"  {passages_ecrits} passages -> {SORTIE.relative_to(ROOT)}")
    print(f"  récapitulatif          -> {RECAP.relative_to(ROOT)}")
    print(f"  en {duree:.0f} s")
    print()
    print("  par type de document :")
    for t, n in par_type.most_common():
        print(f"      {n:>5}  {t}")
    print("  par rubrique :")
    for r, n in par_rubrique.most_common():
        print(f"      {n:>5}  {r}")
    if sans_texte:
        print(f"\n  {sans_texte} document(s) sans texte exploitable, écartés.")
    if sans_rubrique:
        print(f"  {sans_rubrique} document(s) dont aucune rubrique n'a été")
        print("  reconnue : ils ne sont PAS découpés au jugé, ils sont comptés")
        print("  ici et laissés de côté.")
    print()
    print("  RANG 2 : source étrangère. Elle complète la nomenclature")
    print("  algérienne, elle ne la remplace jamais. Chaque passage porte")
    print("  cet avertissement dans son texte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
