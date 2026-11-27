from __future__ import annotations
import csv
from pathlib import Path
from pharmeazor.registry import resolve_drug

OUT = Path("eval/results/trap_eval.md")
INDEX = Path("data/reference/name_index_40molecules.csv")
def get_ids(name: str) -> set[str]:
    normalized = name.lower().replace("-", " ").strip()

    with INDEX.open(encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f)
        return {
            row["drug_id"]
            for row in rows
            if row["alias_normalized"].lower().replace("-", " ").strip()
            == normalized
        }
    
def main() -> int:
    # Test 1: Same name, different capitalization
    q1a = resolve_drug("DOLIPRANE")
    q1b = resolve_drug("doliprane")
    q1c = resolve_drug("Doliprane")

    reformulation_ok = (
        q1a is not None and q1a == q1b == q1c
    )

    # Test 2: Similar names must have different candidate IDs
    doliprane_ids = get_ids("DOLIPRANE")
    dolibien_ids = get_ids("DOLI-BIEN")

    close_names_ok = (
        bool(doliprane_ids)
        and bool(dolibien_ids)
        and doliprane_ids.isdisjoint(dolibien_ids)
    )

    # Generate report
    md = "# Trap evaluation\n\n"

    md += "## Reformulation\n\n"
    md += f"- DOLIPRANE → {q1a}\n"
    md += f"- doliprane → {q1b}\n"
    md += f"- Doliprane → {q1c}\n"
    md += f"- All same? {reformulation_ok}\n\n"

    md += "## Close names\n\n"
    md += f"- DOLIPRANE IDs: {sorted(doliprane_ids)}\n"
    md += f"- DOLI-BIEN IDs: {sorted(dolibien_ids)}\n"
    md += f"- Distinct? {close_names_ok}\n"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(md, encoding="utf-8")

    print("Reformulation:", "OK" if reformulation_ok else "FAIL")
    print("Close names:", "OK" if close_names_ok else "FAIL")

    return 0 if reformulation_ok and close_names_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())