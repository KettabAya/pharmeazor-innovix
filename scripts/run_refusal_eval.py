from __future__ import annotations

import json
from pathlib import Path

from pharmeazor.answer.checks import check_out_of_scope, Verdict

QUESTIONS = [
    {"id": 16, "q": "What is the current retail price of DOLIPRANE 2.4% in Algeria?", "reason": "price"},
    {"id": 17, "q": "Is DOLIPRANE 2.4% currently available in pharmacies near me?", "reason": "availability"},
    {"id": 18, "q": "Which antibiotic should a particular patient take instead of amoxicillin?", "reason": "individualized"},
    {"id": 19, "q": "Which antihypertensive is best for a specific patient?", "reason": "individualized"},
]

OUT = Path("eval/results/refusal_eval.md")

def main() -> int:
    rows = []
    for item in QUESTIONS:
        result = check_out_of_scope(item["q"])
        refused = result.verdict is Verdict.BLOCK          
        rows.append({
            "id": item["id"],
            "question": item["q"],
            "reason": item["reason"],
            "verdict": result.verdict.value,
            "refused": refused,
        })

    md = "# Refusal evaluation — 4 unanswerable questions\n\n"
    md += "| # | Question | Reason | Verdict | Correct? |\n|---|---|---|---|---|\n"
    for r in rows:
        md += f"| {r['id']} | {r['question'][:60]}… | {r['reason']} | {r['verdict']} | {'true' if r['refused'] else 'false'} |\n"

    correct = sum(r["refused"] for r in rows)
    md += f"\n**Refusals correct: {correct}/4.**\n"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(md, encoding="utf-8")
    print(f"Refusals: {correct}/4 — wrote {OUT}")
    return 0 if correct == 4 else 1


if __name__ == "__main__":
    raise SystemExit(main())