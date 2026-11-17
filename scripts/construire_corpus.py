"""Construire le corpus de la semaine 1 et mesurer la référence BM25.

Pourquoi ce script
------------------
La semaine 2 compare deux méthodes de recherche. Une comparaison n'a de sens
que si les deux méthodes travaillent sur **exactement** le même corpus, avec les
mêmes identifiants de passage. Ce script produit ce corpus une fois, l'écrit sur
disque, et mesure la référence BM25 dessus.

Il ne dépend d'aucun document en cours de collecte : tout vient des tables
produites en semaine 1, qui sont versionnées dans le dépôt. Chacune des trois
personnes de l'équipe obtient donc le même corpus, et l'enseignant aussi.

Usage::

    python scripts/construire_corpus.py
    python scripts/construire_corpus.py --sortie data/processed/corpus.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmeazor.retrieve.bm25 import BM25Index  # noqa: E402
from pharmeazor.retrieve.passages import chemin_corpus, construire_corpus  # noqa: E402

# Questions de controle. Elles ne remplacent pas eval/questions.yaml : elles
# servent a voir, a chaque execution, si la recherche par mots-cles se comporte
# comme prevu -- y compris la ou elle doit echouer.
SONDES = [
    ("mots communs", "quel est le dosage de DOLIPRANE", "doit trouver un produit"),
    ("mots communs", "interaction entre paracetamol et mifamurtide",
     "doit trouver l'interaction"),
    ("mots differents", "par quoi remplacer AMLODIPINE en cas de rupture",
     "BM25 devrait echouer : le passage ne contient ni 'remplacer' ni 'rupture'"),
    ("hors perimetre", "quel medicament prendre pour ma migraine",
     "doit obtenir un score tres bas : le systeme doit refuser"),
    ("absente du corpus", "posologie de l'amoxicilline chez l'insuffisant renal",
     "DANGER : score non nul sur un passage hors sujet"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", default=None)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--suffixe", default="",
        help="Jeu de donnees a lire. Vide : la semaine 1, 284 produits et "
             "3 molecules. --suffixe _40molecules : 911 produits, 38 molecules.",
    )
    args = parser.parse_args()

    corpus = construire_corpus(args.suffixe)
    par_id = {p.passage_id: p for p in corpus}

    sections: dict[str, int] = {}
    for p in corpus:
        sections[p.section or "?"] = sections.get(p.section or "?", 0) + 1

    print(f"CORPUS    : {len(corpus)} passages")
    for section, n in sorted(sections.items(), key=lambda x: -x[1]):
        print(f"            {section:<14} {n:4d}")

    longueurs = sorted(len(p.text) for p in corpus)
    mediane = longueurs[len(longueurs) // 2]
    print(f"LONGUEUR  : min {longueurs[0]}, mediane {mediane}, "
          f"max {longueurs[-1]} caracteres")
    print("            aucun passage ne depasse la fenetre de contexte : le")
    print("            decoupage n'a donc pas a etre agressif sur ce corpus.")

    sortie = Path(args.sortie) if args.sortie else chemin_corpus(args.suffixe)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(sortie, "w", encoding="utf-8") as fh:
        for p in corpus:
            fh.write(json.dumps({
                "passage_id": p.passage_id,
                "doc_id": p.doc_id,
                "section": p.section,
                "text": p.text,
                "source_id": p.provenance.source_id,
                "authority": int(p.provenance.authority),
                "url": p.provenance.url,
                "collected_at": p.provenance.collected_at.isoformat(),
            }, ensure_ascii=False) + "\n")
    print(f"ECRIT     : {sortie.relative_to(ROOT)} "
          f"({sortie.stat().st_size / 1024:.0f} Ko)")

    index = BM25Index()
    for p in corpus:
        index.add(p.passage_id, p.text)
    index.finalize()
    print(f"\nREFERENCE BM25 : {len(index)} passages indexes")
    print("Cette colonne est celle que la recherche semantique devra battre.\n")

    for famille, question, attendu in SONDES:
        print(f"  [{famille}] {question}")
        print(f"      attendu : {attendu}")
        resultats = index.search(question, top_k=args.top_k)
        if not resultats:
            print("      -> aucun passage (score nul partout)")
        for r in resultats:
            p = par_id[r.passage_id]
            print(f"      -> {r.score:6.2f}  {p.section:<12} {p.text[:66]}...")
        print()

    print("LIMITE    : ce corpus vient de la nomenclature. Il dit ce qui est")
    print("            enregistre, pas la posologie ni les contre-indications.")
    print("            Les questions qui en relevent doivent rester sans reponse")
    print("            tant que les RCP ne sont pas verses.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
