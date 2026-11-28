from __future__ import annotations

import json
from pathlib import Path

from pharmeazor.answer.checks import Verdict, run_all
from pharmeazor.answer.llm_client import ask_llm
from pharmeazor.normalize.substance import parse_inn
from pharmeazor.registry import interactions_of, resolve_dci, resolve_drug_ids
from pharmeazor.retrieve.bm25 import load_passages_index

PASSAGES_ALL = Path("data/processed/passages_all.jsonl")

REFUSAL = "Information non trouvée dans les sources consultées."


def load_passages_by_id() -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    with PASSAGES_ALL.open(encoding="utf-8") as fh:
        for line in fh:
            p = json.loads(line)
            by_id[str(p["passage_id"])] = p
    return by_id


def extract_question(question: str) -> dict:
    prompt = f"""Extract from this pharmacist question:
Question: {question}
Return JSON only: {{"drugs": [...], "question_type": "..."}}
If no drug, use empty list. If personal recommendation, use "other"."""
    return json.loads(ask_llm(prompt))


def resolve_drugs(drug_names: list[str]) -> list[str]:
    """Tous les identifiants que portent ces noms, pas seulement le premier.

    DOLIPRANE désigne sept produits ; n'en garder qu'un fait disparaître du
    filtre les passages des six autres.
    """
    ids: list[str] = []
    for nom in drug_names:
        for drug_id in resolve_drug_ids(nom):
            if drug_id not in ids:
                ids.append(drug_id)
    return ids


def _base_de(nom: str | None) -> str:
    """La substance débarrassée de son sel : AMOXICILLINE SODIQUE -> AMOXICILLINE.

    Le catalogue écrit le sel que contient le produit, les notices écrivent
    souvent la base, et la base française une troisième forme encore. Comparer
    les écritures telles quelles ne rapproche rien ; comparer les bases, si.
    """
    if not nom:
        return ""
    return (parse_inn(nom).base or nom).strip().upper()


def resolve_substances(drug_names: list[str]) -> list[str]:
    """Les substances derrière ces noms, réduites à leur base."""
    bases = [_base_de(resolve_dci(n)) for n in drug_names]
    return [b for b in bases if b]


def _concerne(p: dict, drug_ids: list[str], substances: list[str]) -> bool:
    """Ce passage parle-t-il bien du médicament demandé ?

    Seuls les passages tirés des RCP portent un ``drug_id`` : ceux de la base
    française et du registre, qui font 88 % du corpus, n'en ont pas et ne
    peuvent en avoir, puisqu'ils décrivent une substance et non une ligne
    précise du catalogue. Filtrer sur le seul identifiant les écarte tous.
    """
    if p.get("drug_id"):
        return p["drug_id"] in drug_ids
    if not substances:
        return False
    base = _base_de(p.get("dci") or p.get("molecule"))
    return bool(base) and base in substances


#: Combien de résultats demander à la recherche quand un médicament est filtré.
#:
#: Le filtre écarte presque tout : 83 % du corpus vient de la base française et
#: concerne d'autres produits. En n'examinant que quinze résultats, on n'en
#: gardait que deux ou trois, et le bon passage restait derrière. Quarante fois
#: le nombre voulu suffit pour que ce qui concerne le médicament remonte —
#: mesuré sur le jeu de questions : 2/15 à quinze résultats, 11/15 à deux cents.
PROFONDEUR_AVEC_FILTRE = 40
PROFONDEUR_SANS_FILTRE = 3


def retrieve(
    question: str,
    drug_ids: list[str],
    top_k: int = 5,
    substances: list[str] | None = None,
) -> list[dict]:
    idx = load_passages_index()
    by_id = load_passages_by_id()
    profondeur = PROFONDEUR_AVEC_FILTRE if drug_ids else PROFONDEUR_SANS_FILTRE
    results = idx.search(question, top_k=top_k * profondeur)
    substances = substances or []
    out: list[dict] = []
    for r in results:
        p = by_id.get(str(r.passage_id))
        if not p:
            continue
        if drug_ids and not _concerne(p, drug_ids, substances):
            continue
        out.append({**p, "score": r.score})
        if len(out) >= top_k:
            break
    return out


def generate_answer(question: str, passages: list[dict], interactions: list[dict]) -> str:
    pt = "\n\n".join(f"[{i + 1}] {p['text'][:400]}" for i, p in enumerate(passages))
    it = "\n".join(f"- {r['inn']} + {r['substance_cible']}: {r['niveau']}" for r in interactions)
    prompt = f"""Answer ONLY from the passages below. If not in passages, say
"{REFUSAL}". Cite [n] for each fact.

QUESTION: {question}
PASSAGES:
{pt}
INTERACTIONS:
{it}
"""
    return ask_llm(prompt)


def _make_citations(passages: list[dict]):

    from pharmeazor.schemas import Citation

    citations = []
    for p in passages:
        try:
            citations.append(Citation(passage=p, quote=p["text"]))
        except TypeError:
            # fallback: the Citation may accept a dict directly
            citations.append(Citation(p))
    return citations


def format_answer(question: str, answer_text: str, passages: list[dict], results) -> dict:
    """Format the final answer from the chain.

    `results` is the list returned by `checks.run_all`.
    """
    verdicts = [r.verdict for r in results]
    blocked = Verdict.BLOCK in verdicts
    flagged = Verdict.FLAG in verdicts

    if blocked:
        status = "refused"
        final = REFUSAL
    elif flagged:
        status = "flagged"
        final = answer_text
    else:
        status = "answered"
        final = answer_text

    return {
        "status": status,
        "question": question,
        "answer": final,
        "citations": [
            {
                "passage_id": p["passage_id"],
                "text": p["text"][:200],
                "source_name": p.get("source_name", ""),
                "authority": p.get("authority", 0),
            }
            for p in passages
        ],
        "checks": [{"verdict": r.verdict.value, "reason": r.reason} for r in results],
    }


def answer(question: str) -> dict:
    extracted = extract_question(question)
    drug_names = extracted.get("drugs", []) or []

    drug_ids = resolve_drugs(drug_names)
    substances = resolve_substances(drug_names)

    print("EXTRACTED DRUGS:", drug_names)
    print("RESOLVED DRUG IDS:", drug_ids)
    print("RESOLVED SUBSTANCES:", substances)

    passages = retrieve(question, drug_ids, substances=substances)

    print("RETRIEVED PASSAGES:", len(passages))

    for p in passages:
        print(
            "PASSAGE:",
            p.get("passage_id"),
            "| DRUG:",
            p.get("drug_id"),
            "| SECTION:",
            p.get("section"),
        )

    interactions: list[dict] = []
    for d in drug_ids:
        interactions.extend(interactions_of(d))
    answer_text = generate_answer(question, passages, interactions)

    citations = _make_citations(passages)
    results = run_all(question, answer_text, citations, est_un_refus=False)

    return format_answer(question, answer_text, passages, results)
