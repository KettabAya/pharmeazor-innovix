"""Montrer, fichier par fichier, ce que chacune a ecrit dans le depot.

Pourquoi ce script
------------------
Le depot contient maintenant plus de 140 fichiers suivis, ecrits a quatre.
Ouvrir l'arborescence ne dit pas qui a fait quoi : un dossier `data/processed`
melange des sorties produites par trois programmes differents.

`dossier_preuves.py` donne deja le total par personne. Celui-ci descend au
fichier, et surtout il separe trois choses qu'on confond vite :

* ce qui est **dans git**, donc visible par l'enseignant depuis GitHub ;
* ce qui est **seulement sur cette machine**, parce que `.gitignore` l'ecarte
  (les classeurs du ministere, les exports dzair, les corpus reconstruits) --
  c'est important a savoir : personne d'autre ne peut relancer la chaine sans
  ces fichiers ;
* ce qui est **produit automatiquement** par une commande, et qu'il ne faut
  donc pas presenter comme du travail ecrit a la main.

L'auteur retenu est celui du DERNIER commit qui a touche le fichier. C'est
imparfait -- une correction d'une ligne fait basculer un fichier -- donc le
script affiche aussi, pour chaque fichier partage, le nombre de lignes
ajoutees par chaque personne, qui est une mesure plus honnete.

Usage::

    python scripts/mon_travail.py
    python scripts/mon_travail.py --moi "Kettab Aya"
    python scripts/mon_travail.py --sortie MON-TRAVAIL.md
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Le nom tel qu'il apparait dans l'historique git.
MOI_PAR_DEFAUT = "Kettab Aya"

# Rangement des fichiers en familles lisibles, dans l'ordre d'affichage.
# Le premier prefixe qui correspond gagne.
FAMILLES: tuple[tuple[str, str], ...] = (
    ("src/pharmeazor/collect/", "Lecture des sources"),
    ("src/pharmeazor/normalize/", "Nettoyage et normalisation"),
    ("src/pharmeazor/reconcile/", "Réconciliation des sources"),
    ("src/pharmeazor/retrieve/", "Recherche et corpus"),
    ("src/pharmeazor/extract/", "Découpage des documents"),
    ("src/pharmeazor/answer/", "Réponse et garde-fous"),
    ("src/pharmeazor/api/", "Interface"),
    ("src/", "Noyau du projet"),
    ("scripts/collecte_alaanour/", "Collecte web (Alaanour)"),
    ("scripts/", "Commandes"),
    ("tests/", "Tests"),
    ("data/reference/", "Livrables de données"),
    ("data/", "Données"),
    ("docs/", "Documentation"),
    ("eval/", "Évaluation"),
    ("config/", "Configuration"),
)

# Ce qui n'est pas du travail d'auteur : réglages d'éditeur, caches.
IGNORES = (".idea/", "__pycache__/", ".gitkeep", "uv.lock", "poetry.lock")

# Fichiers produits par une commande. Les montrer comme du code ecrit a la
# main serait trompeur : ce sont des RESULTATS, et leur valeur est justement
# d'etre reproductibles.
PRODUITS = ("data/reference/", "DOSSIER-DE-PREUVES.md")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout.strip()


def famille(chemin: str) -> str:
    for prefixe, nom in FAMILLES:
        if chemin.startswith(prefixe):
            return nom
    return "Racine du projet"


def interesse(chemin: str) -> bool:
    return not any(mot in chemin for mot in IGNORES)


def dernier_auteur(chemin: str) -> str:
    return git("log", "--format=%an", "-1", "--", chemin) or "(inconnu)"


def lignes_par_auteur() -> dict[str, dict[str, int]]:
    """Pour chaque fichier, combien de lignes chaque personne a ajoutees.

    Lu dans l'historique complet, pas dans l'etat actuel : c'est ce qui
    distingue « j'ai ecrit ce fichier » de « j'y ai corrige une virgule ».
    """
    brut = git("log", "--numstat", "--format=@@%an")
    compte: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    auteur = ""
    for ligne in brut.splitlines():
        if ligne.startswith("@@"):
            auteur = ligne[2:].strip()
            continue
        morceaux = ligne.split("\t")
        if len(morceaux) != 3 or not auteur:
            continue
        ajouts, _, chemin = morceaux
        if ajouts == "-":          # fichier binaire
            continue
        compte[chemin][auteur] += int(ajouts)
    return compte


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--moi", default=MOI_PAR_DEFAUT,
                        help="Nom tel qu'il apparaît dans l'historique git.")
    parser.add_argument("--sortie", default=None,
                        help="Écrire aussi un fichier Markdown.")
    args = parser.parse_args()
    moi = args.moi

    suivis = [f for f in git("ls-files").splitlines() if interesse(f)]
    if not suivis:
        print("Aucun fichier suivi : ce dossier n'est pas un dépôt git.")
        return 1

    ajouts = lignes_par_auteur()
    par_famille: dict[str, list[tuple[str, str, int, int]]] = defaultdict(list)
    for chemin in suivis:
        auteur = dernier_auteur(chemin)
        mes_lignes = ajouts.get(chemin, {}).get(moi, 0)
        autres = sum(n for a, n in ajouts.get(chemin, {}).items() if a != moi)
        par_famille[famille(chemin)].append((chemin, auteur, mes_lignes, autres))

    lignes_out: list[str] = []

    def dire(texte: str = "") -> None:
        print(texte)
        lignes_out.append(texte)

    a_moi = [c for c, a, *_ in
             ((c, a, m, o) for f in par_famille for c, a, m, o in par_famille[f])
             if a == moi]
    dire(f"MON TRAVAIL DANS LE DEPOT — {moi}")
    dire("=" * 64)
    dire()
    dire(f"  {len(a_moi)} fichiers sur {len(suivis)} portent mon nom au dernier commit.")
    dire()

    ordre = [nom for _, nom in FAMILLES] + ["Racine du projet"]
    vues: set[str] = set()
    for nom in ordre:
        if nom in vues or nom not in par_famille:
            continue
        vues.add(nom)
        fichiers = sorted(par_famille[nom])
        miens = [f for f in fichiers if f[1] == moi]
        dire(f"--- {nom}  ({len(miens)}/{len(fichiers)} à moi)")
        for chemin, auteur, mes_lignes, autres in fichiers:
            marque = "  moi " if auteur == moi else "  ·   "
            produit = "  [produit par une commande]" if chemin.startswith(PRODUITS) else ""
            partage = ""
            if mes_lignes and autres:
                partage = f"  [partagé : {mes_lignes} lignes de moi, {autres} des autres]"
            etiquette = "" if auteur == moi else f"  <- {auteur}"
            dire(f"{marque}{chemin}{etiquette}{produit}{partage}")
        dire()

    locaux = [f for f in git("status", "--porcelain", "--ignored", "data").splitlines()
              if f.startswith("!!")]
    if locaux:
        dire("--- Présent sur cette machine, ABSENT de GitHub")
        dire("    (écarté par .gitignore : volumineux, re-téléchargeable, ou")
        dire("     sous licence. Personne d'autre ne peut relancer la chaîne")
        dire("     sans ces fichiers.)")
        for ligne in locaux:
            dire(f"      {ligne[3:].strip()}")
        dire()

    if args.sortie:
        chemin = ROOT / args.sortie
        chemin.write_text("```\n" + "\n".join(lignes_out) + "\n```\n",
                          encoding="utf-8")
        print(f"  écrit : {chemin.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
