from __future__ import annotations

import json
from pathlib import Path

from pharmeazor.answer.checks import (
    check_budget,
    check_numbers,
    check_out_of_scope,
    check_patient_context,
    check_sources_present,
)
from pharmeazor.answer.llm_client import ask_llm, get_call_count
from pharmeazor.registry import interactions_of, resolve_drug
from pharmeazor.retrieve.bm25 import load_passages_index

PASSAGES_ALL = Path("data/processed/passages_all.jsonl")


def load_passages_by_id() -> dict[str, dict]:
    by_id = {}
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
    out = []
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
    it = "\n".join(f"- {r['inn']} + {r['substance_cible']}: {r['niveau']}" for r in interactions)
    prompt = f"""Answer ONLY from the passages below. If not in passages, say
"Information non trouvée dans les sources consultées". Cite [n] for each fact.

QUESTION: {question}
PASSAGES:
{pt}
INTERACTIONS:
{it}
"""
    return ask_llm(prompt)


def run_checks(question, answer, passages):
    return {
        "numbers": check_numbers(answer, passages),
        "sources": check_sources_present(answer, passages),
        "scope": check_out_of_scope(question),
        "patient": check_patient_context(answer, passages),
        "budget": check_budget(get_call_count()),
    }


def format_answer(question, answer, passages, checks):
    blocked = any(c["status"] == "block" for c in checks.values())
    status = (
        "refused"
        if blocked
        else ("flagged" if any(c["status"] == "flag" for c in checks.values()) else "answered")
    )
    return {
        "status": status,
        "question": question,
        "answer": answer if not blocked else "Information non trouvée dans les sources consultées.",
        "citations": [
            {
                "passage_id": p["passage_id"],
                "text": p["text"][:200],
                "source_name": p.get("source_name", ""),
                "authority": p.get("authority", 0),
            }
            for p in passages
        ],
        "checks": checks,
    }


def answer(question: str) -> dict:
    scope = check_out_of_scope(question)
    if scope["status"] == "block":
        return format_answer(question, "", [], {"scope": scope})
    extracted = extract_question(question)
    drug_ids = resolve_drugs(extracted.get("drugs", []))
    passages = retrieve(question, drug_ids)
    interactions = []
    for d in drug_ids:
        interactions.extend(interactions_of(d))
    answer_text = generate_answer(question, passages, interactions)
    checks = run_checks(question, answer_text, passages)
    return format_answer(question, answer_text, passages, checks)
