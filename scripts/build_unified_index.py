"""Réunir en un seul index les passages des RCP, de la base française et du registre.

Trois fichiers entrent, un seul sort. Chacun nomme ses champs à sa façon — « section »
ici, « section_type » là ; « source_id » ici, « source_name » là — alors chaque passage
est ramené à un vocabulaire commun avant d'être écrit, faute de quoi la moitié du corpus
paraît sans provenance.

Sont écartés :
  - les textes rigoureusement identiques, d'où qu'ils viennent
  - les formules de pied de page (pharmacovigilance, en-têtes de RCP)
  - les interactions répétées à l'identique d'une marque à l'autre

Entrée :
  data/processed/passages.jsonl              RCP et notices
  data/processed/passages_bdm.jsonl          base de données publique française
  data/processed/corpus_40molecules.jsonl    registre et nomenclature

Sortie :
  data/processed/passages_all.jsonl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROCESSED = Path("data/processed")
OUT_FILE = PROCESSED / "passages_all.jsonl"

INPUT_FILES = [
    PROCESSED / "passages.jsonl",
    PROCESSED / "passages_bdm.jsonl",
    PROCESSED / "corpus_40molecules.jsonl",
]

# Un champ, plusieurs noms selon le fichier d'origine. Le premier trouvé l'emporte.
ALIASES = {
    "section": ("section", "section_type"),
    "source_id": ("source_id", "source_name"),
    "authority": ("authority", "autorite"),
    "doc_id": ("doc_id", "document"),
    "dci": ("dci", "molecule"),
    "country": ("country", "pays"),
}

# Un passage qui commence par l'une de ces phrases n'apprend rien : il est écarté.
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


def normaliser(p: dict) -> dict:
    """Donner au passage le vocabulaire commun, sans rien perdre de l'ancien.

    Les anciens noms sont conservés à côté des nouveaux : du code écrit avant cette
    unification continue de lire ce qu'il lisait.
    """
    sortie = dict(p)
    for canonique, noms in ALIASES.items():
        for nom in noms:
            valeur = p.get(nom)
            if valeur not in (None, ""):
                sortie[canonique] = valeur
                break
    # « section_type » reste lisible pour le code qui le cherche encore.
    if "section" in sortie:
        sortie.setdefault("section_type", sortie["section"])
    return sortie


def interaction_key(p: dict) -> tuple | None:
    """Deux marques, une même interaction : la reconnaître pour ne la garder qu'une fois."""
    if p.get("section") != "interactions":
        return None
    text = p.get("text", "")
    if " entre " not in text or " et " not in text:
        return None
    niveau = ""
    if "Niveau de l'interaction : " in text:
        niveau = text.split("Niveau de l'interaction : ", 1)[1].split(".", 1)[0].strip()
    return (
        text.split(" entre ", 1)[1].split(" et ", 1)[0].strip(),
        text.split(" et ", 1)[1].split(".", 1)[0].strip(),
        niveau,
    )


def main() -> int:
    manquants = [f for f in INPUT_FILES if not f.exists()]
    if manquants:
        print("Fichiers d'entrée introuvables :", file=sys.stderr)
        for f in manquants:
            print(f"  {f}", file=sys.stderr)
        print(
            "\nL'index serait construit sans eux, et les sections qu'ils seuls "
            "apportent seraient absentes sans que rien ne le signale.",
            file=sys.stderr,
        )
        return 1

    seen_text: set[str] = set()
    seen_interactions: set[tuple] = set()
    merged: list[dict] = []

    for input_file in INPUT_FILES:
        added = skipped_dup = skipped_boiler = skipped_inter = 0
        with input_file.open(encoding="utf-8") as fh:
            for line in fh:
                p = normaliser(json.loads(line))
                text = p.get("text", "")

                if text in seen_text:
                    skipped_dup += 1
                    continue
                if any(text.startswith(prefix) for prefix in BOILERPLATE_PREFIXES):
                    skipped_boiler += 1
                    continue

                ikey = interaction_key(p)
                if ikey and ikey in seen_interactions:
                    skipped_inter += 1
                    continue
                if ikey:
                    seen_interactions.add(ikey)

                seen_text.add(text)
                merged.append(p)
                added += 1

        print(
            f"  {input_file.name}: +{added}, -{skipped_dup} identiques, "
            f"-{skipped_boiler} pieds de page, -{skipped_inter} interactions répétées"
        )

    with OUT_FILE.open("w", encoding="utf-8") as fh:
        for p in merged:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")

    sans_source = sum(1 for p in merged if not p.get("source_id"))
    print(f"\nRéunis : {len(merged)} passages -> {OUT_FILE}")
    if sans_source:
        print(f"Attention : {sans_source} passages sans source_id.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
