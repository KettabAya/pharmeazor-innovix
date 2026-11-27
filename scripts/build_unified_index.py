"""Merge RCP/notice passages and registry passages into one index, deduplicated.

Removes:
  - exact duplicate texts (same text, different source)
  - boilerplate phrases (the generic ANSM footer, the pharmacovigilance footer)
  - repeated interactions (same inn + substance_cible + niveau, listed per brand)

Input:
  data/processed/passages.jsonl              (RCP/notice, 2454)
  data/processed/passages_extra.jsonl        (new RCP, 6441)  ← adjust name
  data/processed/corpus_40molecules.jsonl    (registry, 3596)

Output:
  data/processed/passages_all.jsonl          (deduplicated)
"""

from __future__ import annotations
import json
from pathlib import Path

PROCESSED = Path("data/processed")
OUT_FILE = PROCESSED / "passages_all.jsonl"

INPUT_FILES = [
    PROCESSED / "passages.jsonl",              # old RCP (2454)
    PROCESSED / "passages_extra.jsonl",        # new RCP  ← adjust to real name
    PROCESSED / "corpus_40molecules.jsonl",    # registry (3596)
]

# Boilerplate prefixes — if the passage starts with one of these, drop it.
BOILERPLATE_PREFIXES = (
    "Comme tous les médicaments",
    "ment est importante",
    "Déclaration des effets secondaires",
    "Déclaration des effets indésirables",
    "Que contient cette notice",
    "Informations destinées aux professionnels",
    "ANNEXE I",
    "RESUME DES CARACTERISTIQUES",
)

# Interaction dedup key = (inn, substance_cible, niveau)
def interaction_key(p: dict) -> tuple | None:
    if p.get("section") != "interactions" and p.get("section_type") != "interactions":
        return None
    text = p.get("text", "")
    # text starts with "Interaction médicamenteuse entre <inn> et <substance_cible>."
    # extract by simple split
    if " entre " in text and " et " in text:
        return (text.split(" entre ", 1)[1].split(" et ", 1)[0].strip(),
                text.split(" et ", 1)[1].split(".", 1)[0].strip(),
                text.split("Niveau de l'interaction : ", 1)[-1].split(".", 1)[0].strip()
                if "Niveau de l'interaction :" in text else "")
    return None


def main() -> int:
    seen_text = set()
    seen_interactions = set()
    merged = []

    for input_file in INPUT_FILES:
        if not input_file.exists():
            print(f"  skip (not found): {input_file}")
            continue
        added = 0
        skipped_dup = 0
        skipped_boiler = 0
        skipped_inter = 0
        with input_file.open(encoding="utf-8") as fh:
            for line in fh:
                p = json.loads(line)
                text = p.get("text", "")

                # 1. exact duplicate
                if text in seen_text:
                    skipped_dup += 1
                    continue

                # 2. boilerplate
                if any(text.startswith(prefix) for prefix in BOILERPLATE_PREFIXES):
                    skipped_boiler += 1
                    continue

                # 3. repeated interaction
                ikey = interaction_key(p)
                if ikey and ikey in seen_interactions:
                    skipped_inter += 1
                    continue
                if ikey:
                    seen_interactions.add(ikey)

                seen_text.add(text)
                merged.append(p)
                added += 1

        print(f"  {input_file.name}: +{added}, "
              f"-{skipped_dup} dup, -{skipped_boiler} boiler, -{skipped_inter} interaction")

    with OUT_FILE.open("w", encoding="utf-8") as fh:
        for p in merged:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"\nMerged: {len(merged)} passages → {OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())