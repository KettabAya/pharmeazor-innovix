"""Run BM25 and embeddings on the 19-question subset.

Writes:
  eval/results/retrieval_eval.md
  eval/results/retrieval_eval.json
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from pharmeazor.retrieve.bm25 import load_passages_index
from pharmeazor.retrieve.search_emb import EmbIndex

QUESTIONS = Path("eval/questions_subset.yaml")
PASSAGES = Path("data/processed/passages.jsonl")
RESULTS_MD = Path("eval/results/retrieval_eval.md")
RESULTS_JSON = Path("eval/results/retrieval_eval.json")
SECTION_KEYWORD_FR = {
    "indications": "indications",
    "contre_indications": "contre-indications",
    "posologie": "posologie",
    "interactions": "interactions",
    "effets_indesirables": "effets indésirables",
}

def load_passages_by_id() -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    with PASSAGES.open(encoding="utf-8") as fh:
        for line in fh:
            p = json.loads(line)
            by_id[str(p["passage_id"])] = p
    return by_id


def bm25_pairs(results) -> list[tuple[str, float]]:
    """BM25Result -> (passage_id, score)."""
    return [(str(r.passage_id), r.score) for r in results]


def emb_pairs(results) -> list[tuple[str, float]]:
    """EmbIndex dict -> (passage_id, score)."""
    out = []
    for r in results:
        p = r["passage"]
        out.append((str(p["passage_id"]), r["score"]))
    return out


def rank_of(pairs: list[tuple[str, float]], expected_section: str,
            by_id: dict[str, dict]) -> int | None:
    for i, (pid, _score) in enumerate(pairs, start=1):
        p = by_id.get(pid)
        if p and p.get("section_type") == expected_section:
            return i
    return None


def main() -> int:
    data = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))
    answerable = data["answerable"]
    unanswerable = data["unanswerable"]
    by_id = load_passages_by_id()

    print("Loading BM25...")
    bm25 = load_passages_index()
    print(f"  {len(bm25)} passages indexed.")

    print("Loading embeddings...")
    emb = EmbIndex()

    rows: list[dict] = []
    bm25_hits = 0
    emb_hits = 0

    for q in answerable:
        query = q["question"]
        fr = SECTION_KEYWORD_FR.get(q["expected_section"])
        if fr:
             query = f"{query} {fr}"

        b = bm25_pairs(bm25.search(query, top_k=3))
        e = emb_pairs(emb.search(query, k=3))

        b_rank = rank_of(b, q["expected_section"], by_id)
        e_rank = rank_of(e, q["expected_section"], by_id)
        bm25_hits += b_rank is not None
        emb_hits += e_rank is not None

        b0 = by_id.get(b[0][0]) if b else None
        e0 = by_id.get(e[0][0]) if e else None

        rows.append({
            "id": q["id"],
            "molecule": q["molecule"],
            "question": q["question"],
            "expected_section": q["expected_section"],
            "bm25_rank": b_rank,
            "emb_rank": e_rank,
            "bm25_top1_section": b0.get("section_type") if b0 else None,
            "emb_top1_section": e0.get("section_type") if e0 else None,
            "bm25_score": round(b[0][1], 3) if b else 0,
            "emb_score": round(e[0][1], 3) if e else 0,
        })

    unans_rows = []
    for q in unanswerable:
        b = bm25_pairs(bm25.search(q["question"], top_k=1))
        e = emb_pairs(emb.search(q["question"], k=1))
        unans_rows.append({
            "id": q["id"],
            "question": q["question"],
            "reason": q["reason"],
            "bm25_top1_score": round(b[0][1], 3) if b else 0,
            "emb_top1_score": round(e[0][1], 3) if e else 0,
        })

    n = len(answerable)
    md = f"""# Retrieval evaluation — real question set (19 questions)

Subset of `PharmEazor_Annotated_Questions_10_Medicaments.pdf`.
15 answerable + 4 unanswerable. 51 skipped (molecules not in corpus yet).

## Answerable — BM25 {bm25_hits}/{n}, embeddings {emb_hits}/{n}

| # | Molecule | Expected | BM25 | Emb | BM25 top-1 | Emb top-1 |
|---|---|---|---|---|---|---|
"""
    for r in rows:
        md += (
            f"| {r['id']} | {r['molecule']} | {r['expected_section']} | "
            f"{r['bm25_rank'] or '—'} | {r['emb_rank'] or '—'} | "
            f"{r['bm25_top1_section']} | {r['emb_top1_section']} |\n"
        )

    md += "\n## Unanswerable — top-1 score (high = fail)\n\n"
    md += "| # | Question | Reason | BM25 | Emb |\n|---|---|---|---|---|\n"
    for r in unans_rows:
        md += f"| {r['id']} | {r['question'][:60]}… | {r['reason']} | {r['bm25_top1_score']} | {r['emb_top1_score']} |\n"

    RESULTS_MD.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_MD.write_text(md, encoding="utf-8")
    RESULTS_JSON.write_text(json.dumps(
        {"answerable": rows, "unanswerable": unans_rows},
        indent=2, ensure_ascii=False,
    ), encoding="utf-8")

    print(f"\nWrote {RESULTS_MD}")
    print(f"Wrote {RESULTS_JSON}")
    print(f"\nBM25 top-3: {bm25_hits}/{n}")
    print(f"Embeddings top-3: {emb_hits}/{n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())