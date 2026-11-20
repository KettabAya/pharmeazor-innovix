"""Assembler tout le dossier du projet en un seul PDF.

Contrairement a ``faire_pdf.py``, qui produit un HTML a imprimer soi-meme,
celui-ci ecrit directement un PDF, sans navigateur ni installation.

La chaine est : Markdown -> HTML (bibliotheque ``markdown``) -> PDF
(``pymupdf.Story``). Les deux sont deja dans les dependances du projet.

Le document s'ouvre sur une page de garde et une table des matieres chiffree,
puis enchaine les documents dans l'ordre de lecture : le rapport d'abord, la
defense partie par partie ensuite, les annexes a la fin.

Usage::

    python scripts/faire_pdf_complet.py
    python scripts/faire_pdf_complet.py --sortie ailleurs.pdf
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Ordre de lecture. Un document absent est simplement saute.
DOCUMENTS: list[tuple[str, str]] = [
    ("docs/RAPPORT-SEMAINE-1.md", "Rapport de la semaine 1"),
    ("docs/JOURNAL-TRAITEMENT.md", "Journal du traitement"),
    ("docs/TRAITEMENT-PARTIE-PAR-PARTIE.md", "Le traitement, partie par partie"),
    ("docs/APPRENDRE-A-TRAITER.md", "Apprendre à traiter, du début à la fin"),
    ("docs/RETOUR-ENSEIGNANT-2026-11-15.md", "Retour de l'enseignant et suites"),
    ("docs/LLM-SEUL-RESULTAT.md", "Le modèle seul, sans corpus"),
    ("docs/DATA_SOURCES.md", "Sources et conformité"),
    ("docs/conformite/dzair-pharma-2026-11-15.md", "Relevé de conformité — dzair-pharma"),
    ("DOSSIER-DE-PREUVES.md", "Dossier de preuves"),
    ("docs/MISSION.md", "Mission et question-test"),
    ("docs/ARCHITECTURE.md", "Architecture"),
    ("docs/EVALUATION.md", "Évaluation"),
    ("docs/SEMAINE-1.md", "Plan de la semaine 1"),
    ("docs/SEMAINE-2.md", "Plan de la semaine 2"),
    ("docs/PLAN-TRAITEMENT-DONNEES.md", "Plan de traitement des données"),
]

CSS = """
body { font-family: sans-serif; font-size: 10pt; line-height: 1.45; }
h1 { font-size: 19pt; margin: 0 0 4pt 0; }
h2 { font-size: 14pt; margin: 14pt 0 4pt 0; }
h3 { font-size: 11.5pt; margin: 10pt 0 3pt 0; }
h4 { font-size: 10.5pt; margin: 8pt 0 2pt 0; }
p  { margin: 0 0 5pt 0; }
li { margin: 0 0 2pt 0; }
code { font-family: monospace; font-size: 9pt; }
pre  { font-family: monospace; font-size: 8.5pt; margin: 4pt 0; }
th { font-size: 9pt; text-align: left; }
td { font-size: 9pt; }
blockquote { margin: 4pt 0 4pt 10pt; font-style: italic; }
.titre-doc { font-size: 15pt; margin: 0 0 10pt 0; }
.garde-titre { font-size: 26pt; margin: 0 0 6pt 0; }
.garde-sous  { font-size: 12pt; margin: 0 0 3pt 0; }
.petit { font-size: 9pt; }
"""


def en_html(markdown_source: str) -> str:
    """Markdown -> HTML, en retirant ce que Story ne sait pas rendre."""
    import markdown as md

    # Les emojis et les traits decoratifs passent mal ; on les retire.
    texte = markdown_source.replace("👈", "").replace("⚠️", "Attention :")
    texte = texte.replace("✅", "[fait] ").replace("❌", "[non] ")
    texte = texte.replace("⬜", "[a faire] ").replace("🚨", "Attention : ")
    texte = re.sub(r"^---+$", "", texte, flags=re.M)
    return md.markdown(texte, extensions=["tables", "fenced_code"])


def page_de_garde(nb_documents: int) -> str:
    maintenant = dt.datetime.now()
    return f"""
    <div>
      <p class="garde-titre">Pharmeazor</p>
      <p class="garde-sous">Base de connaissances médicamenteuse
         et assistant à preuves</p>
      <p class="garde-sous">Groupe INNOVIX</p>
      <p class="petit">Module RCR — Projet 2 — M1 Intelligence Artificielle<br>
         Université Constantine 2 Abdelhamid Mehri<br>
         Faculté NTIC — Département IFA</p>
      <p class="petit">Dossier complet, {nb_documents} documents<br>
         Établi le {maintenant:%d/%m/%Y à %H:%M}</p>
    </div>
    """


def table_des_matieres(presents: list[tuple[str, str]]) -> str:
    lignes = "".join(
        f"<li>{titre}<br><span class='petit'>{chemin}</span></li>"
        for chemin, titre in presents
    )
    return f"<h1>Table des matières</h1><ol>{lignes}</ol>"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", default="PHARMEAZOR-DOSSIER-COMPLET.pdf")
    args = parser.parse_args()

    try:
        import pymupdf
    except ImportError:
        print("  pymupdf est requis :  pip install pymupdf")
        return 1

    presents = [(c, t) for c, t in DOCUMENTS if (ROOT / c).exists()]
    absents = [c for c, _ in DOCUMENTS if not (ROOT / c).exists()]
    print(f"  {len(presents)} document(s) a assembler")
    for c in absents:
        print(f"      absent, saute : {c}")

    morceaux = [page_de_garde(len(presents)), table_des_matieres(presents)]
    for i, (chemin, titre) in enumerate(presents, 1):
        source = (ROOT / chemin).read_text(encoding="utf-8")
        # Le titre de premier niveau du fichier est remplace par le notre,
        # numerote, pour que la table des matieres corresponde.
        source = re.sub(r"^#\s+.*$", "", source, count=1, flags=re.M)
        morceaux.append(
            f"<p class='titre-doc'>{i}. {titre}</p>"
            f"<p class='petit'>{chemin}</p>" + en_html(source)
        )
        print(f"      {i:2d}. {titre}")

    html = f"<html><head><style>{CSS}</style></head><body>" \
           + "<p> </p>".join(morceaux) + "</body></html>"

    sortie = Path(args.sortie)
    if not sortie.is_absolute():
        sortie = ROOT / sortie

    story = pymupdf.Story(html=html, user_css=CSS)
    rect = pymupdf.paper_rect("A4")
    zone = rect + (50, 55, -50, -55)
    writer = pymupdf.DocumentWriter(str(sortie))

    pages = 0
    encore = True
    while encore:
        page = writer.begin_page(rect)
        encore, _ = story.place(zone)
        story.draw(page)
        writer.end_page()
        pages += 1
        if pages > 400:  # garde-fou contre une boucle infinie
            print("      arret de securite a 400 pages")
            break
    writer.close()

    print(f"\n  ecrit : {sortie.name}")
    print(f"  {pages} pages, {sortie.stat().st_size/1024:.0f} Ko")
    return 0


if __name__ == "__main__":
    sys.exit(main())
