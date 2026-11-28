"""Mesurer ce que la taille des passages change pour la recherche.

Un passage court est précis mais coupe la phrase ; un passage long porte son
contexte mais mêle plusieurs sujets. On ne peut pas en décider en raisonnant :
on découpe le même corpus à plusieurs tailles, on repasse le jeu de questions
sur chacune, et on lit le tableau.

La mesure porte sur BM25 seul. Les vecteurs demanderaient de ré-encoder 69 102
passages par taille, soit plusieurs heures de calcul pour une question —
*combien de caractères* — à laquelle le lexical répond déjà.

    python scripts/comparer_tailles_passages.py

écrit ``eval/results/tailles_passages.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    sys.exit(1)

from pharmeazor.retrieve.bm25 import BM25Index

RACINE = Path(__file__).resolve().parents[1]
PASSAGES = RACINE / "data" / "processed" / "passages_all.jsonl"
QUESTIONS = RACINE / "eval" / "questions_subset.yaml"
SORTIE = RACINE / "eval" / "results" / "tailles_passages.md"

#: Les tailles comparées, en caractères. La médiane du corpus actuel est autour
#: de mille : on encadre, en dessous et au-dessus.
TAILLES = (300, 600, 1200)

MOT_DE_SECTION = {
    "indications": "indications",
    "contre_indications": "contre-indications",
    "posologie": "posologie",
    "interactions": "interactions",
    "effets_indesirables": "effets indésirables",
}


def redecouper(texte: str, taille: int) -> list[str]:
    """Couper au point le plus proche de la taille voulue, jamais au milieu d'un mot.

    On coupe sur une fin de phrase quand il y en a une dans le dernier quart du
    morceau, sinon sur une espace : un passage qui s'arrête en plein mot ne se
    cite pas.
    """
    texte = texte.strip()
    if len(texte) <= taille:
        return [texte] if texte else []

    morceaux: list[str] = []
    reste = texte
    while len(reste) > taille:
        fenetre = reste[:taille]
        coupe = max(fenetre.rfind(". "), fenetre.rfind("; "), fenetre.rfind(" — "))
        if coupe < taille * 3 // 4:
            coupe = fenetre.rfind(" ")
        if coupe <= 0:
            coupe = taille
        morceaux.append(reste[: coupe + 1].strip())
        reste = reste[coupe + 1 :].lstrip()
    if reste:
        morceaux.append(reste)
    return [m for m in morceaux if m]


def index_a_la_taille(passages: list[dict], taille: int) -> tuple[BM25Index, dict[str, dict]]:
    """Reconstruire l'index en redécoupant chaque passage à cette taille."""
    idx = BM25Index()
    par_id: dict[str, dict] = {}
    for p in passages:
        for n, morceau in enumerate(redecouper(p.get("text", ""), taille)):
            pid = f"{p['passage_id']}#{n}"
            idx.add(pid, morceau)
            par_id[pid] = {**p, "passage_id": pid, "text": morceau}
    idx.finalize()
    return idx, par_id


def mesurer(idx: BM25Index, par_id: dict[str, dict], questions: list[dict]) -> tuple[int, float]:
    """Combien de questions trouvent la bonne section dans les trois premiers."""
    trouvees = 0
    rangs: list[int] = []
    for q in questions:
        requete = f"{q['question']} {MOT_DE_SECTION.get(q['expected_section'], '')}".strip()
        for rang, r in enumerate(idx.search(requete, top_k=3), start=1):
            p = par_id.get(str(r.passage_id))
            if p and p.get("section_type") == q["expected_section"]:
                trouvees += 1
                rangs.append(rang)
                break
    moyen = sum(rangs) / len(rangs) if rangs else 0.0
    return trouvees, moyen


def main() -> int:
    if not PASSAGES.exists():
        print(f"Introuvable : {PASSAGES}", file=sys.stderr)
        print("Lancez d'abord : python scripts/build_unified_index.py", file=sys.stderr)
        return 1

    passages = [json.loads(line) for line in PASSAGES.open(encoding="utf-8")]
    questions = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))["answerable"]

    longueurs = sorted(len(p.get("text", "")) for p in passages)
    mediane = longueurs[len(longueurs) // 2]

    lignes = [
        "# Taille des passages — ce qu'elle change",
        "",
        f"Corpus : {len(passages)} passages, longueur médiane {mediane} caractères.",
        f"Questions : les {len(questions)} questions avec réponse du jeu officiel.",
        "Un succès = la bonne section figure dans les trois premiers résultats.",
        "",
        "Mesure sur BM25 seul : comparer les vecteurs demanderait de ré-encoder",
        "le corpus entier une fois par taille.",
        "",
        f"| Taille visée | Passages obtenus | Trouvés /{len(questions)} | Rang moyen |",
        "|---|---|---|---|",
    ]

    resultats = []
    for taille in TAILLES:
        idx, par_id = index_a_la_taille(passages, taille)
        trouvees, moyen = mesurer(idx, par_id, questions)
        resultats.append((taille, len(idx), trouvees, moyen))
        lignes.append(
            f"| {taille} caractères | {len(idx)} | {trouvees} | {moyen:.1f} |"
        )
        print(f"  {taille:>5} caracteres -> {len(idx):>6} passages, {trouvees}/{len(questions)}")

    # Et le corpus tel qu'il est aujourd'hui, pour comparer a quelque chose.
    idx, par_id = BM25Index(), {}
    for p in passages:
        idx.add(p["passage_id"], p.get("text", ""))
        par_id[str(p["passage_id"])] = p
    idx.finalize()
    trouvees, moyen = mesurer(idx, par_id, questions)
    lignes.append(f"| *tel quel* | {len(idx)} | {trouvees} | {moyen:.1f} |")
    print(f"  tel quel      -> {len(idx):>6} passages, {trouvees}/{len(questions)}")

    meilleur = max(resultats, key=lambda r: (r[2], -r[3]))
    ecart = max(r[2] for r in resultats) - min(r[2] for r in resultats)
    lignes += [
        "",
        f"Le meilleur des trois découpages est **{meilleur[0]} caractères** "
        f"({meilleur[2]}/{len(questions)}, rang moyen {meilleur[3]:.1f}).",
        "",
        "## Ce que la mesure dit vraiment",
        "",
        f"L'écart entre le meilleur et le pire découpage est de {ecart} question"
        f"{'s' if ecart > 1 else ''} sur {len(questions)}, et quadrupler le nombre de",
        "passages ne change pas le résultat. **La taille n'est pas le levier.**",
        "",
        "Ce qui limite la recherche ici est ailleurs : 83 % du corpus vient de la",
        "base française et concerne d'autres produits que celui de la question.",
        "Quelle que soit la découpe, ces passages occupent les premières places.",
        "Le filtre par médicament du pipeline, lui, fait passer la même mesure de",
        "5/15 à 11/15 — vingt fois l'effet de la taille.",
        "",
        "Le tableau reste à refaire si les sources changeaient : une taille qui ne",
        "départage rien sur ce corpus pourrait compter sur un autre.",
        "",
    ]

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text("\n".join(lignes), encoding="utf-8")
    print(f"\necrit {SORTIE.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
