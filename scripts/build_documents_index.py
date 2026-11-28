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
NOTICES_DIR = Path("data/raw/notices")


def strip_accents(s: str) -> str:
    d = unicodedata.normalize("NFKD", s)
    return "".join(c for c in d if not unicodedata.combining(c))


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", strip_accents(s).lower()).strip()


def load_rules() -> list[dict]:
    return yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))


def lire_provenance(doc: str) -> dict:
    """Ce que le collecteur a noté à côté du document : url, date, pays.

    Chaque document de ``data/raw/notices/`` est accompagné d'un ``.json`` qui
    dit d'où il vient et quand il a été pris. Sans lui, la date devait être
    écrite en dur, la même pour tous — alors qu'il y en a sept différentes — et
    l'url, que la règle d'or du projet demande de citer, manquait tout
    simplement.
    """
    chemin = NOTICES_DIR / f"{doc}.json"
    if not chemin.exists():
        return {}
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


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
                # Le dosage et la forme : ce qui sépare deux produits de même
                # substance, et donc ce qui permet de ne pas en choisir un au
                # hasard quand le nom du document les mentionne.
                "strength": row.get("strength_raw", "").strip().upper().replace(" ", ""),
                "form": row.get("form", "").strip().upper(),
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


def _dosages_du_nom(doc_lower: str) -> set[str]:
    """Les dosages écrits dans le nom du document : ``75mg`` -> ``75MG``.

    Les noms de fichiers séparent par des soulignés, que l'expression régulière
    compte parmi les lettres : sans les remplacer, ``100mg_notice`` ne se
    terminerait jamais et aucun dosage ne serait lu.
    """
    texte = doc_lower.replace("_", " ").replace("-", " ")
    return {
        f"{n}{u}".upper()
        for n, u in re.findall(r"(\d+)\s*(mg|g|ml|ui|pct)\b", texte)
    }


def match_drug(
    doc_name: str, rules: list[dict], drugs: list[dict]
) -> tuple[dict | None, dict | None, int]:
    """Rattacher un document à un produit du catalogue.

    La substance ne suffit pas à désigner un produit : 144 lignes du catalogue
    portent PARACETAMOL, du comprimé à la suspension buvable, et prendre la
    première revient à tirer au sort. Le nom du fichier en dit plus — la marque
    et le dosage y figurent — alors on s'en sert pour resserrer, dans cet ordre.

    Rend le produit, la règle de source, et le nombre de produits qui restaient
    indiscernables : zéro ambiguïté, ou le compte de ce qui n'a pas pu être
    départagé.
    """
    doc_lower = doc_name.lower()
    rule = next((r for r in rules if r["match"] in doc_lower), None)
    if rule is None:
        return None, None, 0

    mots = doc_lower.replace("-", " ")

    candidats = [
        d
        for d in drugs
        if d["inn_norm"]
        and any(len(t) >= 5 and t in mots for t in d["inn_norm"].split())
    ]
    if not candidats:
        return None, rule, 0

    # La marque, quand le catalogue la connaît et que le nom la porte.
    par_marque = [d for d in candidats if d["brand_norm"] and d["brand_norm"] in mots]
    if par_marque:
        candidats = par_marque

    # Le dosage, qui sépare un 75 mg d'un 500 mg.
    dosages = _dosages_du_nom(doc_lower)
    if dosages:
        par_dosage = [d for d in candidats if d["strength"] in dosages]
        if par_dosage:
            candidats = par_dosage

    # Toujours plusieurs : on en prend un, mais on dit combien restaient.
    candidats.sort(key=lambda d: d["drug_id"])
    return candidats[0], rule, len(candidats) - 1


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
    ambigus: list[str] = []

    for sf in section_files:
        data = json.loads(sf.read_text(encoding="utf-8"))
        doc = data.get("document") or sf.stem.removesuffix("_sections")
        drug, rule, restants = match_drug(doc, rules, drugs)

        if rule is None:
            skipped.append(f"{doc}: no rule matched (add a rule in {RULES_FILE})")
            continue
        if drug is None:
            skipped.append(f"{doc}: no drug matched in {DRUGS_CSV}")
            continue

        extra = next(
            (c for c in collect
             if c["molecule"] == drug["inn_norm"] and c["marque_norm"] and c["marque_norm"] in doc.lower()),
            None,
        )

        if restants:
            ambigus.append(f"{doc}: {restants + 1} produits portent ce nom, {drug['drug_id']} retenu")

        provenance = lire_provenance(doc)

        index[doc] = {
            "drug_id": drug["drug_id"],
            "dci": drug["inn"],
            "therapeutic_class": drug["therapeutic_class"],
            "source_name": rule["source_name"],
            "authority": rule["authority"],
            "language": provenance.get("language") or rule.get("language", "fr"),
            "collected_at": provenance.get("collected_at", ""),
            "url": provenance.get("url", ""),
            "country": provenance.get("country", ""),
            "document_type": provenance.get("document_type", ""),
            "n_enregistrement": extra["n_enregistrement"] if extra else "",
            "laboratoire": extra["laboratoire"] if extra else "",
            "dosage": extra["dosage"] if extra else "",
            "forme": extra["forme"] if extra else "",
            "produits_indiscernables": restants,
        }

    OUT.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(index)} entries to {OUT}")

    if ambigus:
        print("\nPlusieurs produits portaient le meme nom (le choix est partiel) :")
        for line in ambigus:
            print("  -", line)

    if skipped:
        print("\nNOT indexed (fix these):")
        for line in skipped:
            print("  -", line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())