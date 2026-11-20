from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

PASSAGES_FILE = Path("data/processed/passages.jsonl")

# French stopwords (enough for the test and the queries we have).
STOPWORDS = {
    "au",
    "aux",
    "avec",
    "ce",
    "ces",
    "dans",
    "de",
    "des",
    "du",
    "elle",
    "en",
    "et",
    "eux",
    "il",
    "ils",
    "je",
    "la",
    "le",
    "les",
    "leur",
    "lui",
    "ma",
    "mais",
    "me",
    "meme",
    "mes",
    "moi",
    "mon",
    "ne",
    "nos",
    "notre",
    "nous",
    "on",
    "ou",
    "par",
    "pas",
    "pour",
    "que",
    "qui",
    "sa",
    "se",
    "ses",
    "son",
    "sur",
    "ta",
    "te",
    "tes",
    "toi",
    "ton",
    "tu",
    "un",
    "une",
    "vos",
    "votre",
    "vous",
    "y",
    "a",
    "ete",
    "etee",
    "etees",
    "etes",
    "etant",
    "suis",
    "es",
    "est",
    "sommes",
    "sont",
    "sera",
    "seront",
    "d",
    "l",
    "j",
    "t",
    "m",
    "n",
    "s",
    "c",
    "qu",
}


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return [t for t in text.split() if len(t) >= 2 and t not in STOPWORDS]


@dataclass
class BM25Result:
    passage_id: str
    text: str
    score: float


class BM25Index:
    def __init__(self):
        self._ids: list[str] = []
        self._texts: list[str] = []
        self._tokens: list[list[str]] = []
        self._bm25: BM25Okapi | None = None

    def add(self, passage_id: str, text: str) -> None:
        if not text.strip():
            return
        self._ids.append(str(passage_id))
        self._texts.append(text)
        self._tokens.append(tokenize(text))
        self._bm25 = None

    def finalize(self) -> BM25Index:
        if self._tokens:
            self._bm25 = BM25Okapi(self._tokens)
        return self

    def __len__(self) -> int:
        return len(self._ids)

    def search(self, question: str, top_k: int = 5) -> list[BM25Result]:
        if self._bm25 is None or not self._ids:
            return []
        q_tokens = tokenize(question)
        if not q_tokens:
            return []

        scores = self._bm25.get_scores(q_tokens)
        order = sorted(range(len(self._ids)), key=lambda i: -scores[i])

        results: list[BM25Result] = []
        for i in order:
            if scores[i] <= 0:
                break
            results.append(
                BM25Result(
                    passage_id=self._ids[i],
                    text=self._texts[i],
                    score=float(scores[i]),
                )
            )
            if len(results) >= top_k:
                break
        return results


def load_passages_index(passages_file: Path = PASSAGES_FILE) -> BM25Index:
    idx = load_passages_index()
    with Path(passages_file).open(encoding="utf-8") as fh:
        for line in fh:
            p = json.loads(line)
            idx.add(p["passage_id"], p["text"])
    idx.finalize()
    return idx


if __name__ == "__main__":
    idx = load_passages_index()
    print(f"Indexed {len(idx)} passages.")
    for query in [
        "amlodipine contre-indications",
        "amlodipine posologie",
        "amoxicilline posologie enfant",
        "amoxicilline effets indésirables",
        "paracetamol posologie enfant",
        "paracetamol contre-indications",
    ]:
        print(f"\n=== {query}")
        results = idx.search(query, top_k=3)
        if not results:
            print("  (no result)")
            continue
        for r in results:
            print(f"  [{r.score:.2f}] {r.passage_id}")
            print(f"    {r.text[:120].strip()}...")
