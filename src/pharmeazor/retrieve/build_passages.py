import json
from pathlib import Path

MAX_CHARS = 700
OVERLAP = 100
MIN_CHARS = 80

PROCESSED = Path("data/processed")
SECTIONS_DIR = PROCESSED / "sections"
INDEX_FILE = PROCESSED / "documents_index.json"
OUT_FILE = PROCESSED / "passages.jsonl"

SECTION_TYPE_MAP = {
    "indications": "indications",
    "posologie": "posologie",
    "contre_indications": "contre_indications",
    "interactions": "interactions",
    "effets_indesirables": "effets_indesirables",
}


def chunk_text(text):
    """Split text into overlapping passages."""

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + MAX_CHARS, len(text))

        if end < len(text):
            boundary = text.rfind(". ", start, end)

            if boundary == -1:
                boundary = text.rfind("\n", start, end)
            if boundary == -1:
                boundary = text.rfind(" ", start, end)

            if boundary > start:
                end = boundary + 1

        chunk = text[start:end]

        if len(chunk.strip()) >= MIN_CHARS:
            chunks.append((chunk, start, end))

        if end >= len(text):
            break

        start = max(start + 1, end - OVERLAP)

    return chunks


def build_passages():
    if not INDEX_FILE.exists():
        raise FileNotFoundError(f"Missing {INDEX_FILE}")

    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    passage_id = 0
    total_documents = 0

    with OUT_FILE.open("w", encoding="utf-8") as output:
        for file in sorted(SECTIONS_DIR.glob("*_sections.json")):
            data = json.loads(file.read_text(encoding="utf-8"))

            doc_name = data["document"]
            meta = index.get(doc_name)

            if not meta:
                print(f"Skipping {doc_name}: not found in index")
                continue

            total_documents += 1

            for sec_key, sec_text in data["sections"].items():
                sec_type = SECTION_TYPE_MAP.get(sec_key)

                if not sec_type or not sec_text.strip():
                    continue

                for chunk, start, end in chunk_text(sec_text):
                    assert sec_text[start:end] == chunk, "Verbatim check failed"

                    passage_id += 1

                    passage = {
                        "passage_id": passage_id,
                        "document": doc_name,
                        "drug_id": meta["drug_id"],
                        "dci": meta["dci"],
                        "source_name": meta["source_name"],
                        "authority": meta["authority"],
                        "section_type": sec_type,
                        "text": chunk,
                        "original_text": sec_text,
                        "char_start": start,
                        "char_end": end,
                    }

                    output.write(json.dumps(passage, ensure_ascii=False) + "\n")

    print(f"Created {passage_id} passages from {total_documents} documents.")

    return passage_id


if __name__ == "__main__":
    build_passages()
