"""Montrer des passages un par un, pour écrire les questions d'évaluation.

À quoi ça sert
--------------
Écrire 15 questions devant une page blanche est difficile. Écrire une question
devant un passage est facile : on le lit, et on se demande « quelle question un
pharmacien poserait-il pour tomber là-dessus ? »

Ce script affiche des passages tirés du corpus, avec leur identifiant, prêts à
être recopiés dans ``eval/questions.yaml``.

Usage::

    python scripts/voir_passages.py                 # 5 passages varies
    python scripts/voir_passages.py --combien 10
    python scripts/voir_passages.py --section interactions
    python scripts/voir_passages.py --chercher AMOXICILLINE
    python scripts/voir_passages.py --modele         # le gabarit YAML a recopier
"""

from __future__ import annotations

import argparse
import random
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmeazor.retrieve.passages import construire_corpus  # noqa: E402

LARGEUR = 78

MODELE = """\
# A recopier dans eval/questions.yaml, a la suite des autres.
# Remplacez ce qui est entre <>.

  - id: Q0XX
    level: 1                      # 1 direct | 2 croise | 3 contexte patient
    question: "<la question, telle qu'un pharmacien la poserait>"
    expected_answer: "<la reponse, en une phrase>"
    reference_passage: <l'identifiant affiche par ce script>
    reference_source: nomenclature

# Et pour une question SANS reponse dans le corpus -- il en faut au moins 3 :

  - id: Q0YY
    level: absent
    question: "<une vraie question de pharmacien, mais hors de nos documents>"
    expected_behaviour: declare_missing
    reference_passage: null
    reference_source: null
    note: "<pourquoi le corpus ne peut pas y repondre>"
"""


def afficher(p, numero: int) -> None:
    print("=" * LARGEUR)
    print(f"PASSAGE {numero}   [{p.section}]")
    print(f"identifiant : {p.passage_id}")
    print(f"source      : {p.provenance.cite()}")
    print("-" * LARGEUR)
    for ligne in textwrap.wrap(p.text, LARGEUR):
        print(ligne)
    print("-" * LARGEUR)
    print("Quelle question un pharmacien poserait-il pour trouver ce passage ?")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--combien", type=int, default=5)
    parser.add_argument("--section", default=None,
                        help="produit | equivalents | interactions")
    parser.add_argument("--chercher", default=None,
                        help="n'afficher que les passages contenant ce mot")
    parser.add_argument("--modele", action="store_true",
                        help="afficher le gabarit YAML et s'arreter")
    parser.add_argument("--graine", type=int, default=None,
                        help="pour retomber sur les memes passages")
    parser.add_argument(
        "--suffixe", default="",
        help="Jeu de donnees a lire. Vide : la semaine 1, 284 produits et "
             "3 molecules. --suffixe _40molecules : 914 produits, 38 molecules.",
    )
    args = parser.parse_args()

    if args.modele:
        print(MODELE)
        return 0

    corpus = construire_corpus(args.suffixe)

    choix = corpus
    if args.section:
        choix = [p for p in choix if p.section == args.section]
    if args.chercher:
        besoin = args.chercher.upper()
        choix = [p for p in choix if besoin in p.text.upper()]

    if not choix:
        print("Aucun passage ne correspond. Sections disponibles :")
        for s in sorted({p.section or "?" for p in corpus}):
            print(f"  - {s}")
        return 1

    if args.section or args.chercher:
        # Filtre explicite : on montre le debut de la selection, dans l'ordre.
        selection = choix[: args.combien]
    else:
        # Sans filtre, on varie les sections pour ne pas ecrire 15 questions
        # qui se ressemblent toutes.
        rng = random.Random(args.graine)
        par_section: dict[str, list] = {}
        for p in choix:
            par_section.setdefault(p.section or "?", []).append(p)
        selection = []
        sections = sorted(par_section)
        while len(selection) < args.combien and any(par_section.values()):
            for s in sections:
                if par_section[s] and len(selection) < args.combien:
                    selection.append(par_section[s].pop(rng.randrange(len(par_section[s]))))

    for i, p in enumerate(selection, start=1):
        afficher(p, i)

    print(f"{len(selection)} passage(s) sur {len(choix)} disponible(s).")
    print()
    print("Pour le gabarit a recopier dans eval/questions.yaml :")
    print("    python scripts/voir_passages.py --modele")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
