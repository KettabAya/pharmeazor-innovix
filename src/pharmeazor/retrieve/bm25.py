from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from rank_bm25 import BM25Okapi

PASSAGES_FILE = Path("data/processed/passages.jsonl")


def tokenize(text: str) -> list[str]:
    """Lowercase, strip accents, split on non-alphanumerics, drop very short tokens."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return [t for t in text.split() if len(t) >= 2]


class BM25Index:
    def __init__(self, passages_file: Path = PASSAGES_FILE):
        self.passages = [json.loads(l) for l in passages_file.open(encoding="utf-8")]
        self.tokenized = [tokenize(p["text"]) for p in self.passages]
        self.bm25 = BM25Okapi(self.tokenized)

    def search(self, question: str, k: int = 5, drug_ids: list[str] | None = None):
        q_tokens = tokenize(question)
        if not q_tokens:
            return []
        scores = self.bm25.get_scores(q_tokens)

        order = sorted(range(len(self.passages)), key=lambda i: -scores[i])
        results = []
        for i in order:
            if scores[i] <= 0:
                break   # below this, BM25 has no match — do not return noise
            p = self.passages[i]
            if drug_ids and p["drug_id"] not in drug_ids:
                continue
            results.append({
                "passage": p,
                "score": float(scores[i]),
                "section_id": p["passage_id"],
                "document": p["document"],
                "authority": p["authority"],
            })
            if len(results) >= k:
                break
        return results


if __name__ == "__main__":
    idx = BM25Index()
    print(f"Indexed {len(idx.passages)} passages.")
    for query in [
        "amlodipine contre-indications",
        "amlodipine posologie",
        "amoxicilline posologie enfant",
        "amoxicilline effets indésirables",
        "paracetamol posologie enfant",
        "paracetamol contre-indications",
    ]:
        print(f"\n=== {query}")
        results = idx.search(query, k=3)
        if not results:
            print("  (no result)")
            continue
        for r in results:
            print(f"  [{r['score']:.2f}] {r['document']} / {r['passage']['section_type']}")
            print(f"    {r['passage']['text'][:120].strip()}...")