"""Produire un dossier de preuves horodaté, extrait du dépôt lui-même.

Rassemble en un seul fichier ce qu'un correcteur peut vouloir vérifier sans
cloner le projet : la contribution de chaque personne relevée dans l'historique
Git, l'inventaire des livrables avec leur empreinte, le résultat de la suite de
tests, et les commandes qui reproduisent chaque chiffre.

Rien n'est saisi à la main : tout est lu dans le dépôt au moment de
l'exécution. Un dossier de preuves qu'on écrirait soi-même ne prouverait rien.

Usage::

    python scripts/dossier_preuves.py
    python scripts/dossier_preuves.py --sortie DOSSIER.md
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LIVRABLES = [
    ("data/reference/drugs_semaine1.csv", "table produit nettoyée"),
    ("data/reference/name_index.csv", "dictionnaire des noms"),
    ("data/reference/equivalents_semaine1.csv", "groupes d'équivalents"),
    ("data/reference/interactions_semaine1.csv", "interactions avec niveau ANSM"),
    ("data/reference/retraits_semaine1.csv", "produits sortis du marché"),
    ("data/reference/desaccords_versions.csv", "désaccords entre versions datées"),
    # Le périmètre élargi aux 38 molécules. Il coexiste avec la semaine 1 :
    # les deux jeux sont livrés, et leurs empreintes distinctes le prouvent.
    ("data/reference/drugs_40molecules.csv", "table produit, 38 molécules"),
    ("data/reference/name_index_40molecules.csv", "dictionnaire des noms, 38 molécules"),
    ("data/reference/equivalents_40molecules.csv", "groupes d'équivalents, 38 molécules"),
    ("data/reference/interactions_40molecules.csv", "interactions, 38 molécules"),
    ("data/reference/retraits_40molecules.csv", "produits sortis du marché, 38 molécules"),
    ("data/reference/desaccords_versions_40molecules.csv", "désaccords entre versions, 38 molécules"),
    ("data/reference/mouvements_versions_40molecules.csv", "produits apparus et disparus entre versions"),
    ("data/reference/source_registry.yaml", "registre des sources et conformité"),
    ("data/reference/documents_a_collecter.csv", "liste de collecte des notices"),
    ("eval/llm_alone_test.json", "trace du test du modèle seul"),
    ("preprocessing.ipynb", "notebook de traitement"),
]

COMMANDES = [
    ("git log --format='%an %ad %s' --date=short", "qui a contribué, et quand"),
    ("python scripts/build_week1.py", "régénère table, dictionnaire, équivalents, interactions"),
    ("python scripts/comparer_versions.py", "les désaccords entre versions du registre"),
    ("python scripts/verifier_echantillon.py", "tire 5 produits à vérifier à la main"),
    ("pytest", "la suite de tests"),
]


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", errors="replace").stdout.strip()
    except FileNotFoundError:
        return ""


def empreinte(chemin: Path) -> str:
    """SHA-256 tronquée : permet de prouver qu'un fichier n'a pas bougé."""
    h = hashlib.sha256()
    h.update(chemin.read_bytes())
    return h.hexdigest()[:16]


def parcourir_historique() -> dict[str, dict]:
    """Relever, par personne, ses commits, ses lignes et ses fichiers.

    ``%aN`` applique ``.mailmap`` : quelqu'un qui a poussé sous plusieurs noms
    ou adresses est compté une seule fois, sous le nom retenu. Les commits de
    fusion sont ignorés pour les lignes, sinon le travail fusionné serait
    attribué à celle qui a fusionné.
    """
    # Separateur : US (unite), absent de tout nom d'auteur et de tout chemin.
    # NUL serait plus sur encore, mais Windows l'interdit dans un argument.
    sep = "\x1f"
    brut = git("log", "--no-merges", "--date=short",
               f"--format={sep}%aN{sep}%ad", "--numstat")
    stats: dict[str, dict] = {}
    courant = None
    for ligne in brut.splitlines():
        if ligne.startswith(sep):
            _, auteur, date = ligne.split(sep)
            if not auteur:
                courant = None
                continue
            courant = stats.setdefault(auteur, {
                "commits": 0, "ajouts": 0, "retraits": 0,
                "fichiers": set(), "dates": [],
            })
            courant["commits"] += 1
            courant["dates"].append(date)
            continue
        if courant is None or not ligne.strip():
            continue
        morceaux = ligne.split("\t")
        if len(morceaux) >= 3:
            # "-" au lieu d'un nombre signale un fichier binaire.
            if morceaux[0].isdigit():
                courant["ajouts"] += int(morceaux[0])
            if morceaux[1].isdigit():
                courant["retraits"] += int(morceaux[1])
            courant["fichiers"].add(morceaux[2])
    return stats


def lignes_csv(chemin: Path) -> int:
    with open(chemin, encoding="utf-8", newline="") as fh:
        return max(0, sum(1 for _ in csv.reader(fh)) - 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dossier de preuves horodaté.")
    parser.add_argument("--sortie", default="DOSSIER-DE-PREUVES.md")
    args = parser.parse_args()

    maintenant = dt.datetime.now()
    out: list[str] = [
        "# Dossier de preuves — Pharmeazor",
        "",
        f"Généré le **{maintenant:%d/%m/%Y à %H:%M}** depuis le dépôt lui-même.",
        "Aucune valeur n'est saisie à la main : tout est relevé à l'exécution.",
        "",
        f"- Dépôt : `{git('config', '--get', 'remote.origin.url') or '(local)'}`",
        f"- Branche : `{git('rev-parse', '--abbrev-ref', 'HEAD')}`",
        f"- Commit : `{git('rev-parse', '--short', 'HEAD')}`",
        f"- Total : **{git('rev-list', '--count', 'HEAD')} commits**, "
        f"{len(git('ls-files').splitlines())} fichiers suivis",
        "",
        "---",
        "",
        "## 1. Contribution par personne",
        "",
        "Relevée dans l'historique Git. Un commit porte un auteur, une date et une",
        "empreinte : ces chiffres ne sont pas déclarés, ils sont constatés.",
        "",
        "| Auteur | Commits | Lignes ajoutées | Lignes retirées | Première | Dernière |",
        "|---|---:|---:|---:|---|---|",
    ]

    # Un seul parcours de l'historique, attribue au nom retenu par .mailmap.
    #
    # La version precedente listait les auteurs avec %an, qui ignore le
    # mailmap, puis comptait avec `--author=`, dont la correspondance est
    # approximative. Resultat : une personne ayant pousse sous deux noms
    # apparaissait deux fois, avec des chiffres identiques -- elle comptait
    # donc double dans un document remis a l'enseignant. %aN applique le
    # mailmap, et le comptage se fait ici plutot que par filtres successifs.
    stats = parcourir_historique()

    auteurs = sorted(stats, key=lambda a: -stats[a]["commits"])
    for auteur in auteurs:
        s = stats[auteur]
        out.append(f"| **{auteur}** | {s['commits']} | +{s['ajouts']:,} | "
                   f"−{s['retraits']:,} | {min(s['dates'])} | {max(s['dates'])} |")

    out += ["", "### Fichiers touchés par chaque personne", ""]
    for auteur in auteurs:
        fichiers = sorted(stats[auteur]["fichiers"])
        out.append(f"**{auteur}** — {len(fichiers)} fichiers")
        out.append("")
        for f in fichiers[:14]:
            out.append(f"- `{f}`")
        if len(fichiers) > 14:
            out.append(f"- *… et {len(fichiers) - 14} autres*")
        out.append("")

    out += [
        "---",
        "",
        "## 2. Livrables, avec leur empreinte",
        "",
        "L'empreinte SHA-256 permet de vérifier qu'un fichier est bien celui-ci et",
        "qu'il n'a pas été modifié depuis.",
        "",
        "| Fichier | Contenu | Lignes | Empreinte |",
        "|---|---|---:|---|",
    ]
    for rel, desc in LIVRABLES:
        chemin = ROOT / rel
        if not chemin.exists():
            out.append(f"| `{rel}` | {desc} | — | *absent* |")
            continue
        n = lignes_csv(chemin) if rel.endswith(".csv") else "—"
        out.append(f"| `{rel}` | {desc} | {n} | `{empreinte(chemin)}` |")

    out += ["", "---", "", "## 3. Suite de tests", ""]
    res = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header"],
                         cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    derniere = [x for x in (res.stdout or "").strip().splitlines() if x.strip()]
    out += [
        "```",
        *(derniere[-6:] if derniere else ["(pytest indisponible)"]),
        "```",
        "",
        f"Code de sortie : **{res.returncode}** " +
        ("— tous les tests passent." if res.returncode == 0 else "— **des tests échouent**."),
        "",
        "---",
        "",
        "## 4. Reproduire chaque chiffre",
        "",
        "| Commande | Ce qu'elle établit |",
        "|---|---|",
    ]
    for cmd, quoi in COMMANDES:
        out.append(f"| `{cmd}` | {quoi} |")

    out += [
        "",
        "---",
        "",
        "## 5. Les vingt derniers commits",
        "",
        "```",
        git("log", "-20", "--format=%h  %ad  %-14an  %s", "--date=short"),
        "```",
        "",
        "---",
        "",
        "*Pour régénérer ce dossier : `python scripts/dossier_preuves.py`*",
        "",
    ]

    sortie = ROOT / args.sortie
    sortie.write_text("\n".join(out), encoding="utf-8")
    print(f"  ecrit : {sortie.name}  ({sortie.stat().st_size / 1024:.0f} Ko)")
    print(f"  {len([a for a in auteurs if a])} auteur(s), "
          f"{len([r for r, _ in LIVRABLES if (ROOT / r).exists()])} livrable(s), "
          f"tests : {'OK' if res.returncode == 0 else 'ECHEC'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
