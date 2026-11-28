from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

PASSAGES_FILE = Path("data/processed/passages_all.jsonl")
EMB_FILE = Path("data/processed/embeddings.npy")
IDS_FILE = Path("data/processed/embedding_ids.json")
MODEL_NAME = "intfloat/multilingual-e5-base"


class EmbIndex:
    def _cache_utilisable(self) -> bool:
        """Le cache a-t-il été calculé sur ce corpus-ci ?

        ``search`` lit ``self.passages[i]`` avec un indice venu de la matrice :
        si les deux ne décrivent pas la même liste, chaque recherche rend des
        passages sans rapport avec la question, et rien ne le signale. C'est
        arrivé : le corpus est passé de 11 791 à 69 102 passages et le cache,
        versionné, est resté celui d'avant.
        """
        if not (EMB_FILE.exists() and IDS_FILE.exists()):
            return False
        try:
            ids = json.loads(IDS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False
        if len(ids) != len(self.passages):
            print(
                f"Cached embeddings ignored: {len(ids)} vectors for "
                f"{len(self.passages)} passages. Re-encoding."
            )
            return False
        attendus = [p["passage_id"] for p in self.passages]
        if ids != attendus:
            print("Cached embeddings ignored: passage ids differ. Re-encoding.")
            return False
        return True

    def __init__(self, passages_file: Path = PASSAGES_FILE):
        self.passages = [json.loads(line) for line in passages_file.open(encoding="utf-8")]
        self.model = SentenceTransformer(MODEL_NAME)

        if self._cache_utilisable():
            self.emb = np.load(EMB_FILE)
            self.ids = json.loads(IDS_FILE.read_text(encoding="utf-8"))
            print(f"Loaded cached embeddings: {self.emb.shape}")
        else:
            print(f"Encoding {len(self.passages)} passages...")
            texts = [f"passage: {p['text']}" for p in self.passages]
            self.emb = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                normalize_embeddings=True,
            )
            np.save(EMB_FILE, self.emb)
            self.ids = [p["passage_id"] for p in self.passages]
            IDS_FILE.write_text(json.dumps(self.ids), encoding="utf-8")
            print(f"Saved embeddings to {EMB_FILE}")

    def search(self, question: str, k: int = 5):
        q = self.model.encode([f"query: {question}"], normalize_embeddings=True)[0]
        scores = self.emb @ q
        order = np.argsort(-scores)[:k]
        results = []
        for i in order:
            p = self.passages[i]
            results.append(
                {
                    "passage": p,
                    "score": float(scores[i]),
                    "section_id": p["passage_id"],
                    "document": p.get("document", ""),
                    "authority": p.get("authority", 0),
                }
            )
        return results
