from __future__ import annotations

import json
from pathlib import Path

from pharmeazor.answer.checks import run_all, Verdict
from pharmeazor.answer.llm_client import ask_llm
from pharmeazor.registry import interactions_of, resolve_drug
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
    return [d for d in (resolve_drug(n) for n in drug_names) if d]


def retrieve(question: str, drug_ids: list[str], top_k: int = 5) -> list[dict]:
    idx = load_passages_index()
    by_id = load_passages_by_id()
    results = idx.search(question, top_k=top_k * 3)
    out: list[dict] = []
    for r in results:
        p = by_id.get(str(r.passage_id))
        if not p:
            continue
        if drug_ids and p.get("drug_id") not in drug_ids:
            continue
        out.append({**p, "score": r.score})
        if len(out) >= top_k:
            break
    return out


def generate_answer(question: str, passages: list[dict], interactions: list[dict]) -> str:
    pt = "\n\n".join(f"[{i + 1}] {p['text'][:400]}" for i, p in enumerate(passages))
    it = "\n".join(
        f"- {r['inn']} + {r['substance_cible']}: {r['niveau']}"
        for r in interactions
    )
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
        "checks": [
            {"verdict": r.verdict.value, "reason": r.reason}
            for r in results
        ],
    }


def answer(question: str) -> dict:
    extracted = extract_question(question)
    drug_names = extracted.get("drugs", []) or []

    drug_ids = resolve_drugs(drug_names)

    print("EXTRACTED DRUGS:", drug_names)
    print("RESOLVED DRUG IDS:", drug_ids)

    passages = retrieve(question, drug_ids)

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