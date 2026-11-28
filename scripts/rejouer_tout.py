"""Rejouer toute la chaîne, des sources brutes aux mesures, en une commande.

    python scripts/rejouer_tout.py

Les étapes s'enchaînent dans l'ordre où elles se nourrissent : les tables, puis
les passages, puis l'index unique, puis les mesures. La première qui échoue
arrête tout — une étape qui continue sans son entrée produit un résultat
silencieusement faux, et c'est exactement ce qui est arrivé : l'index s'est
construit sans la base française parce qu'un fichier manquant était seulement
signalé, pas bloquant.

Options :
    --sans-collecte   partir des tables déjà écrites, sans relire data/raw/
    --sans-vecteurs   sauter l'évaluation dense (sentence-transformers absent)
    --lister          afficher les étapes et ce qu'il leur faut, sans rien faire
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Etape:
    titre: str
    script: str
    arguments: list[str] = field(default_factory=list)
    #: Ce qu'il faut avoir sous la main pour que l'étape ait un sens.
    requiert: list[str] = field(default_factory=list)
    #: Ce qu'elle écrit, pour que le lecteur sache où regarder.
    produit: list[str] = field(default_factory=list)
    #: Vraie pour les étapes qui relisent data/raw/, sautées par --sans-collecte.
    collecte: bool = False
    #: Vraie pour les étapes qui ont besoin de sentence-transformers.
    vecteurs: bool = False


ETAPES: tuple[Etape, ...] = (
    Etape(
        "Tables de référence",
        "build_week1.py",
        ["--suffixe", "_40molecules"],
        requiert=["data/raw/nomenclature", "data/raw/dzair"],
        produit=["data/reference/drugs_40molecules.csv", "data/reference/name_index_40molecules.csv"],
        collecte=True,
    ),
    Etape(
        "Passages de la base française",
        "build_index.py",
        requiert=["data/raw/bdm"],
        produit=["data/processed/passages_bdm.jsonl"],
        collecte=True,
    ),
    Etape(
        "Passages du registre",
        "construire_corpus.py",
        requiert=["data/reference/drugs_40molecules.csv"],
        produit=["data/processed/corpus_40molecules.jsonl"],
    ),
    Etape(
        "Index unique",
        "build_unified_index.py",
        requiert=[
            "data/processed/passages.jsonl",
            "data/processed/passages_bdm.jsonl",
            "data/processed/corpus_40molecules.jsonl",
        ],
        produit=["data/processed/passages_all.jsonl"],
    ),
    Etape(
        "Index des documents",
        "build_documents_index.py",
        requiert=["data/processed/sections", "data/reference/drugs_40molecules.csv"],
        produit=["data/processed/documents_index.json"],
    ),
    Etape(
        "Tableau de conformité",
        "tableau_conformite.py",
        requiert=["data/reference/source_registry.yaml"],
        produit=["docs/CONFORMITE.md"],
    ),
    Etape(
        "Refus sur les questions sans réponse",
        "run_refusal_eval.py",
        requiert=["eval/questions_subset.yaml"],
        produit=["eval/results/refusal_eval.md"],
    ),
    Etape(
        "Reformulation et noms proches",
        "run_trap_eval.py",
        requiert=["data/reference/name_index_40molecules.csv"],
        produit=["eval/results/trap_eval.md"],
    ),
    Etape(
        "Taille des passages",
        "comparer_tailles_passages.py",
        requiert=["data/processed/passages_all.jsonl"],
        produit=["eval/results/tailles_passages.md"],
    ),
    Etape(
        "Recherche : lexicale contre vecteurs",
        "run_retrieval_eval.py",
        requiert=["data/processed/passages_all.jsonl"],
        produit=["eval/results/retrieval_eval.md"],
        vecteurs=True,
    ),
)


def manquant(etape: Etape) -> list[str]:
    return [c for c in etape.requiert if not (RACINE / c).exists()]


def lister() -> int:
    print("Les étapes, dans l'ordre :\n")
    for n, e in enumerate(ETAPES, start=1):
        marques = []
        if e.collecte:
            marques.append("collecte")
        if e.vecteurs:
            marques.append("vecteurs")
        suffixe = f"  [{', '.join(marques)}]" if marques else ""
        absent = manquant(e)
        etat = "  ← il manque " + ", ".join(absent) if absent else ""
        print(f"  {n}. {e.titre}{suffixe}{etat}")
        print(f"     {e.script} -> {', '.join(e.produit)}")
    return 0


def executer(etape: Etape) -> bool:
    commande = [sys.executable, str(RACINE / "scripts" / etape.script), *etape.arguments]
    debut = time.monotonic()
    issue = subprocess.run(commande, cwd=RACINE)
    duree = time.monotonic() - debut
    if issue.returncode != 0:
        print(f"\n  ÉCHEC : {etape.titre} (code {issue.returncode}, {duree:.0f} s)")
        return False
    print(f"  fait en {duree:.0f} s -> {', '.join(etape.produit)}")
    return True


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--sans-collecte", action="store_true",
                           help="partir des tables déjà écrites")
    analyseur.add_argument("--sans-vecteurs", action="store_true",
                           help="sauter l'évaluation dense")
    analyseur.add_argument("--lister", action="store_true",
                           help="afficher les étapes sans rien exécuter")
    options = analyseur.parse_args()

    if options.lister:
        return lister()

    etapes = [
        e for e in ETAPES
        if not (options.sans_collecte and e.collecte)
        and not (options.sans_vecteurs and e.vecteurs)
    ]

    # La première étape ne peut compter sur personne : si son entrée manque,
    # autant le dire avant d'avoir écrit quoi que ce soit.
    if etapes and (absents := manquant(etapes[0])):
        print(f"Il manque, pour « {etapes[0].titre} » : {', '.join(absents)}", file=sys.stderr)
        print("Ces dossiers sont au dépôt : git pull, ou --sans-collecte pour",
              "partir des tables déjà écrites.", file=sys.stderr)
        return 1

    total = len(etapes)
    debut = time.monotonic()
    for n, etape in enumerate(etapes, start=1):
        print(f"\n[{n}/{total}] {etape.titre}")
        absents = manquant(etape)
        if absents:
            print(f"  il manque : {', '.join(absents)}", file=sys.stderr)
            print("  (une étape précédente devait l'écrire — la chaîne s'arrête ici)",
                  file=sys.stderr)
            return 1
        if not executer(etape):
            return 1

    print(f"\nToute la chaîne a été rejouée en {(time.monotonic() - debut) / 60:.0f} min.")
    print("Les mesures sont dans eval/results/, le tableau de conformité dans docs/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
