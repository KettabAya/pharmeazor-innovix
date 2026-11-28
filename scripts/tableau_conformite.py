"""Écrire le tableau de conformité demandé : une ligne par source.

L'enseignant demande, pour chaque source : le cas (1, 2 ou 3), la copie datée du
robots.txt et des conditions, la méthode de collecte et le nombre de documents.
Tout cela existe déjà, éparpillé — le registre des sources, les relevés de
``docs/conformite/``, les dossiers de ``data/raw/``. Un tableau écrit à la main
vieillirait dès la prochaine collecte ; celui-ci se régénère.

    python scripts/tableau_conformite.py

écrit ``docs/CONFORMITE.md``.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    sys.exit(1)

RACINE = Path(__file__).resolve().parents[1]
REGISTRE = RACINE / "data" / "reference" / "source_registry.yaml"
RELEVES = RACINE / "docs" / "conformite"
SORTIE = RACINE / "docs" / "CONFORMITE.md"

# Les trois cas, tels que l'enseignant les a poses le 21/11 :
#
#   1. Rien ne l'interdit        -> automatisation limitee et respectueuse
#                                   (cache, delais, pas de collecte massive)
#   2. Conditions floues         -> collecte manuelle
#   3. Le site l'interdit        -> manuelle obligatoire, ou source ecartee
#
# Le cas ne se deduit pas d'un seul champ : il tient au robots.txt ET aux
# conditions d'utilisation. Il est donc pose ici, source par source, avec sa
# raison — un jugement se relit, il ne se calcule pas.
CAS: dict[str, tuple[int, str]] = {
    "anpp_rcp": (3, "Collecte manuelle obligatoire, demandée par l'enseignant."),
    "nomenclature": (1, "robots.txt n'interdit rien ; téléchargement manuel des fichiers publiés."),
    "ansm_thesaurus": (1, "robots.txt n'interdit rien ; thésaurus consulté, non aspiré."),
    "ansm_bdpm": (1, "robots.txt autorise les chemins publics ; réutilisation sous attribution."),
    "dzair_pharma": (3, "robots.txt interdit /api/, /admin et /diff. Recoupement manuel seulement."),
    "pharmnet": (2, "Aucune CGU identifiée au 13/11/2026 : conditions floues."),
    "ema": (2, "Conditions de réutilisation non confirmées pour un usage dérivé."),
    "dailymed": (2, "Droits de réutilisation des labels non confirmés."),
    "vidal": (3, "Les CGU interdisent toute reproduction sans consentement."),
    "medalgerie": (3, "robots.txt non vérifiable (certificat TLS invalide au 15/11/2026)."),
    "forums": (3, "Écartés du corpus par la règle du projet."),
}

# Ce que chaque source a effectivement fourni, et ou cela se trouve.
DOCUMENTS: dict[str, tuple[str, str]] = {
    "anpp_rcp": ("data/raw/notices", "*_rcp.pdf"),
    "nomenclature": ("data/raw/nomenclature", "*.xlsx"),
    "ansm_bdpm": ("data/raw/bdm", "**/*.pdf"),
    "dzair_pharma": ("data/raw/dzair", "*.json"),
    "pharmnet": ("data/raw/fiches_dzair/fiches", "*.json"),
}


def compter(source_id: str) -> str:
    """Combien de documents cette source a fournis, tels qu'ils sont au dépôt."""
    entree = DOCUMENTS.get(source_id)
    if not entree:
        return "—"
    dossier, motif = entree
    chemin = RACINE / dossier
    if not chemin.exists():
        return "0 *(non présent sur cette machine)*"
    return str(len(list(chemin.glob(motif))))


def releve(source: dict) -> str:
    """Le lien vers la copie datée du robots.txt, si elle a été prise."""
    base = (source.get("base_url") or "").removeprefix("https://").removeprefix("http://")
    hote = base.rstrip("/").split("/")[0]
    if not hote:
        return "—"
    for fichier in sorted(RELEVES.glob(f"robots-{hote}-*.txt")):
        # Le nom se termine par la date : robots-<hote>-AAAA-MM-JJ.txt
        date = fichier.stem[-10:]
        return f"[{date}](conformite/{fichier.name})"
    return "*non relevé*"


def methode(source: dict, cas: int) -> str:
    acces = source.get("access", "")
    if acces == "forbidden":
        return "écartée"
    if cas == 1:
        return "automatisée (cache, délais)"
    return "manuelle"


def main() -> int:
    sources = yaml.safe_load(REGISTRE.read_text(encoding="utf-8"))["sources"]

    lignes = [
        "# Tableau de conformité par source",
        "",
        "Régénéré par `python scripts/tableau_conformite.py`.",
        "",
        "Les trois cas, tels que posés le 21/11/2026 :",
        "",
        "1. **Rien ne l'interdit** — automatisation limitée et respectueuse",
        "   (cache, délais, pas de collecte massive).",
        "2. **Conditions floues** — collecte manuelle.",
        "3. **Le site l'interdit** — collecte manuelle obligatoire, ou source écartée.",
        "",
        "| Source | Pays | Rang | Cas | robots.txt daté | Méthode | Documents |",
        "|---|---|---|---|---|---|---|",
    ]

    raisons: list[str] = []
    for s in sources:
        sid = s.get("source_id", "?")
        cas, raison = CAS.get(sid, (2, "Cas non statué."))
        lignes.append(
            f"| `{sid}` | {s.get('country', '—')} | {s.get('authority', '—')} | {cas} | "
            f"{releve(s)} | {methode(s, cas)} | {compter(sid)} |"
        )
        raisons.append(f"- **`{sid}`** — cas {cas}. {raison}")

    lignes += ["", "## Pourquoi ce cas, source par source", ""]
    lignes += raisons
    lignes += [
        "",
        "## Ce qui n'est pas utilisé",
        "",
        "**Les données de démonstration d'interactions de Pharm'Net ne sont pas",
        "utilisées.** Les 1 510 interactions de `data/reference/interactions_40molecules.csv`",
        "portent toutes `source_origine = ANSM` et `source_relais = dzair_pharma` ;",
        "le fichier ne contient aucune occurrence de Pharm'Net. Ce qui vient de",
        "Pharm'Net, ce sont 853 fiches produit et 270 photographies, sans interaction.",
        "",
        "Sont également écartés : les prix, les stocks, les forums, les blogs et les",
        "réseaux sociaux.",
        "",
        "## Les copies datées",
        "",
        "Les relevés intégraux sont dans [`conformite/`](conformite/), à la date où",
        "ils ont été pris. Le relevé détaillé de dzair-pharma, demandé en semaine 1,",
        "est dans [`conformite/dzair-pharma-2026-11-15.md`](conformite/dzair-pharma-2026-11-15.md).",
        "",
    ]

    SORTIE.write_text("\n".join(lignes), encoding="utf-8")
    print(f"ecrit {SORTIE.relative_to(RACINE)} — {len(sources)} sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
