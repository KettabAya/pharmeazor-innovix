from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

PASSAGES_FILE = Path("data/processed/passages.jsonl")
EMB_FILE = Path("data/processed/embeddings.npy")
IDS_FILE = Path("data/processed/embedding_ids.json")
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class EmbIndex:
    def __init__(self, passages_file: Path = PASSAGES_FILE):
        self.passages = [json.loads(l) for l in passages_file.open(encoding="utf-8")]

        if EMB_FILE.exists() and IDS_FILE.exists():
            self.emb = np.load(EMB_FILE)
            self.ids = json.loads(IDS_FILE.read_text(encoding="utf-8"))
            print(f"Loaded cached embeddings: {self.emb.shape}")
        else:
            print(f"Encoding {len(self.passages)} passages... (one-time, ~1 min)")
            model = SentenceTransformer(MODEL_NAME)
            texts = [p["text"] for p in self.passages]
            self.emb = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
            np.save(EMB_FILE, self.emb)
            self.ids = [p["passage_id"] for p in self.passages]
            IDS_FILE.write_text(json.dumps(self.ids), encoding="utf-8")
            print(f"Saved embeddings to {EMB_FILE}")

        self.model = SentenceTransformer(MODEL_NAME)

    def search(self, question: str, k: int = 5):
        q = self.model.encode([question], normalize_embeddings=True)[0]
        scores = self.emb @ q
        order = np.argsort(-scores)[:k]
        results = []
        for i in order:
            p = self.passages[i]
            results.append({
                "passage": p,
                "score": float(scores[i]),
                "section_id": p["passage_id"],
                "document": p["document"],
                "authority": p["authority"],
            })
        return results


if __name__ == "__main__":
    idx = EmbIndex()
    for query in [
        "amlodipine contre-indications",
        "amlodipine posologie",
        "amoxicilline posologie enfant",
        "amoxicilline effets indésirables",
        "paracetamol posologie enfant",
        "paracetamol contre-indications",
    ]:
        print(f"\n=== {query}")
        for r in idx.search(query, k=3):
            print(f"  [{r['score']:.3f}] {r['document']} / {r['passage']['section_type']}")