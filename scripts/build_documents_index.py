from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    sys.exit(1)

PROCESSED = Path("data/processed")
SECTIONS_DIR = PROCESSED / "sections"         
REFERENCE = Path("data/reference")
OUT = PROCESSED / "documents_index.json"
RULES_FILE = REFERENCE / "source_rules.yaml"

DRUGS_CSV = REFERENCE / "drugs_40molecules.csv"
COLLECT_CSV = REFERENCE / "documents_a_collecter.csv"


def strip_accents(s: str) -> str:
    d = unicodedata.normalize("NFKD", s)
    return "".join(c for c in d if not unicodedata.combining(c))


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", strip_accents(s).lower()).strip()


def load_rules() -> list[dict]:
    return yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))


def load_drugs() -> list[dict]:
    rows: list[dict] = []
    with DRUGS_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["drug_id"] or row["drug_id"].startswith("#"):
                continue
            rows.append({
                "drug_id": row["drug_id"].strip(),
                "inn": row["inn"].strip(),
                "inn_norm": norm(row["inn"]),
                "brand_name": row.get("brand_name", "").strip(),
                "brand_norm": norm(row.get("brand_name", "")),
                "therapeutic_class": row.get("therapeutic_class", "").strip(),
            })
    return rows


def load_collect() -> list[dict]:
    if not COLLECT_CSV.exists():
        return []
    rows: list[dict] = []
    with COLLECT_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({
                "molecule": norm(row.get("molecule", "")),
                "marque": row.get("marque_a_chercher", "").strip(),
                "marque_norm": norm(row.get("marque_a_chercher", "")),
                "n_enregistrement": row.get("n_enregistrement", "").strip(),
                "dosage": row.get("dosage", "").strip(),
                "forme": row.get("forme", "").strip(),
                "laboratoire": row.get("laboratoire", "").strip(),
            })
    return rows


def match_drug(doc_name: str, rules: list[dict], drugs: list[dict]) -> tuple[dict | None, dict | None]:
    doc_lower = doc_name.lower()
    rule = next((r for r in rules if r["match"] in doc_lower), None)
    if rule is None:
        return None, None

    for d in drugs:
        if not d["inn_norm"]:
            continue
        for token in d["inn_norm"].split():
            if len(token) >= 5 and token in doc_lower.replace("-", " "):
                return d, rule
    return None, rule       


def main() -> int:
    rules = load_rules()
    drugs = load_drugs()
    collect = load_collect()

    section_files = sorted(SECTIONS_DIR.glob("*_sections.json"))
    if not section_files:
        print(f"No *_sections.json in {SECTIONS_DIR}/", file=sys.stderr)
        return 1

    index: dict[str, dict] = {}
    skipped: list[str] = []

    for sf in section_files:
        data = json.loads(sf.read_text(encoding="utf-8"))
        doc = data.get("document") or sf.stem.removesuffix("_sections")
        drug, rule = match_drug(doc, rules, drugs)

        if rule is None:
            skipped.append(f"{doc}: no rule matched (add a rule in {RULES_FILE})")
            continue
        if drug is None:
            skipped.append(f"{doc}: no drug matched in {DRUGS_CSV}")
            continue

        brand = doc.split("_")[1] if "_" in doc else ""
        extra = next(
            (c for c in collect
             if c["molecule"] == drug["inn_norm"] and c["marque_norm"] and c["marque_norm"] in doc.lower()),
            None,
        )

        index[doc] = {
            "drug_id": drug["drug_id"],
            "dci": drug["inn"],
            "therapeutic_class": drug["therapeutic_class"],
            "source_name": rule["source_name"],
            "authority": rule["authority"],
            "language": rule.get("language", "fr"),
            "collected_at": "2026-11-17",
            "n_enregistrement": extra["n_enregistrement"] if extra else "",
            "laboratoire": extra["laboratoire"] if extra else "",
            "dosage": extra["dosage"] if extra else "",
            "forme": extra["forme"] if extra else "",
        }

    OUT.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(index)} entries to {OUT}")

    if skipped:
        print("\nNOT indexed (fix these):")
        for line in skipped:
            print("  -", line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())