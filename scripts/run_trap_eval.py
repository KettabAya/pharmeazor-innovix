from __future__ import annotations
import json
from pathlib import Path

from pharmeazor.registry import resolve_drug

OUT = Path("eval/results/trap_eval.md")

def main() -> int:
    q1a = resolve_drug("DOLIPRANE")
    q1b = resolve_drug("doliprane 2.4%")
    q1c = resolve_drug("DOLIPRAN")
    reformulation_ok = q1a == q1b == q1c

    a = resolve_drug("DOLIPRANE")
    b = resolve_drug("DOLIDOL")
    trap_ok = a != b and a is not None and b is not None

    md = "# Trap evaluation\n\n"
    md += "## Reformulation (same drug, 3 spellings)\n\n"
    md += f"- DOLIPRANE → {q1a}\n- doliprane 2.4% → {q1b}\n- DOLIPRAN → {q1c}\n"
    md += f"- All same? {'true' if reformulation_ok else 'false'}\n\n"
    md += "## Close names (must distinguish)\n\n"
    md += f"- DOLIPRANE → {a}\n- DOLIDOL → {b}\n"
    md += f"- Distinct? {'true' if trap_ok else 'false'}\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(md, encoding="utf-8")
    print(f"Reformulation: {'OK' if reformulation_ok else 'FAIL'}")
    print(f"Close names:  {'OK' if trap_ok else 'FAIL'}")
    return 0 if reformulation_ok and trap_ok else 1

if __name__ == "__main__":
    raise SystemExit(main())