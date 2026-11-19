"""Exploiter les fiches produit collectées par l'équipe, une par médicament.

Ce que c'est, et ce que ce n'est pas
------------------------------------
``data/raw/fiches_dzair/fiches/`` contient 1 179 fiches, une par produit,
collectées sur dzair-pharma. Elles sont **plus minces** que l'extraction
``row_data`` déjà exploitée : trois champs d'identité, un bloc d'interactions
et un bloc d'équivalents.

Le bloc d'interactions est inutilisable, et c'est mesuré :

    1 103 fiches sur 1 103 portent le même texte --
    « Réservé aux professionnels de santé. Le détail des interactions est
    accessible aux médecins et pharmaciens inscrits, après vérification du
    numéro d'inscription à l'Ordre. »

Ce n'est pas une lacune de la collecte : le site réserve cette rubrique. On
le consigne comme un fait sur la source, pas comme une donnée manquante.

Ce qu'elles apportent, et qui n'est NULLE PART ailleurs
--------------------------------------------------------
Le bloc « équivalents thérapeutiques » est rempli dans **986 fiches** et
annonce **7 172 produits**. Chaque entrée porte deux champs que ni la
nomenclature ni l'extraction row_data ne contiennent :

* ``substituable_indique`` — le site signale la substitution comme indiquée
  ou non ;
* ``local`` — produit fabriqué en Algérie.

Le premier est précieux **et délicat**. Nos groupes d'équivalents refusent
explicitement de se prononcer sur l'interchangeabilité : c'est un jugement
pharmaceutique, pas une décision de programme. Une source qui, elle, se
prononce, ne doit donc pas être recopiée comme une vérité — mais elle vaut
d'être enregistrée, avec son rang, pour que le pharmacien voie qu'elle
existe et qu'elle dit quoi.

Usage::

    python scripts/lire_fiches_dzair.py
    python scripts/lire_fiches_dzair.py --suffixe _40molecules
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmeazor.config import MOLECULES_PROJET  # noqa: E402
from pharmeazor.normalize.substance import concerne_molecule  # noqa: E402

FICHES = ROOT / "data" / "raw" / "fiches_dzair" / "fiches"
IMAGES = ROOT / "data" / "raw" / "fiches_dzair" / "images"
REFERENCE = ROOT / "data" / "reference"

CHAMPS = [
    "produit", "dosage", "dci", "code_dci",
    "equivalent_nom", "equivalent_dosage", "equivalent_laboratoire",
    "equivalent_pays", "equivalent_local", "substituable_indique",
    "a_une_photo", "source", "autorite",
]


def aplatir(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", str(texte or ""))
    sans = "".join(c for c in decompose if not unicodedata.combining(c))
    return sans.upper().replace(" ", "").replace("-", "").strip()


_UUID = re.compile(r"_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
# Un dosage en fin de nom : 500MG, 1G, 1%_(10MG_ML), 100MG_SACHET...
_DOSAGE_FINAL = re.compile(r"_[0-9(][^_]*$")


def _marque_de_l_image(chemin: Path) -> str:
    """Retrouver la marque dans « Aspegic_Adulte_1G_c8dda55e-....png ».

    La marque contient elle-meme des souligne. Un decoupage sur le PREMIER
    souligne ne rendait que « Aspegic », et seuls 97 produits sur 483
    trouvaient leur photo. On retire donc l'uuid par la fin, puis tout ce qui
    commence par un chiffre ou une parenthese -- c'est le dosage -- et on
    garde ce qui reste.
    """
    nom = _UUID.sub("", chemin.stem)
    while True:
        reduit = _DOSAGE_FINAL.sub("", nom)
        if reduit == nom or not reduit:
            break
        nom = reduit
    return aplatir(nom.replace("_", " "))


def bloc_equivalents(fiche: dict) -> dict:
    """Retrouver le bloc, quelle que soit la forme de la cle accentuee.

    La cle s'ecrit « equivalents therapeutiques » avec des accents, et le
    fichier peut la stocker en forme composee ou decomposee. Une comparaison
    litterale echoue alors silencieusement -- c'est arrive le 19/11/2026 et
    j'en avais conclu, a tort, que ces blocs etaient tous vides.
    """
    for cle, valeur in fiche.items():
        if "quivalents" in cle and isinstance(valeur, dict):
            return valeur
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suffixe", default="_40molecules")
    parser.add_argument("--toutes-molecules", action="store_true")
    args = parser.parse_args()

    if not FICHES.exists():
        print(f"{FICHES} est absent.")
        return 1

    photos = {_marque_de_l_image(p) for p in IMAGES.glob("*.png")} \
        if IMAGES.exists() else set()

    lignes: list[list[str]] = []
    paywall = sans_equivalent = hors_perimetre = 0
    substituables: Counter = Counter()
    vus_produits: set[str] = set()

    for chemin in sorted(FICHES.glob("*.json")):
        try:
            fiche = json.loads(chemin.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(fiche, dict) or not fiche.get("nom_commercial"):
            continue

        dci = fiche.get("dci", "")
        if not args.toutes_molecules and not concerne_molecule(dci, MOLECULES_PROJET):
            hors_perimetre += 1
            continue

        interactions = next(
            (v for k, v in fiche.items() if k.lower().startswith("interactions")), "")
        if isinstance(interactions, str) and "professionnels de sant" in interactions:
            paywall += 1

        bloc = bloc_equivalents(fiche)
        code = re.sub(r"\s+", " ", str(bloc.get("code_dci", "") or "")).strip()
        produits = bloc.get("produits") or []
        if not produits:
            sans_equivalent += 1

        nom = fiche["nom_commercial"]
        vus_produits.add(aplatir(nom))
        for equivalent in produits:
            if not isinstance(equivalent, dict):
                continue
            substituable = equivalent.get("substituable_indique")
            substituables[str(substituable)] += 1
            lignes.append([
                nom, fiche.get("dosage", ""), dci, code,
                equivalent.get("nom", ""), equivalent.get("dosage", ""),
                equivalent.get("laboratoire", ""), equivalent.get("pays", ""),
                "oui" if equivalent.get("local") else "non",
                "oui" if substituable else "non",
                "oui" if aplatir(nom) in photos else "non",
                "dzair_pharma", "professionnelle (rang 1)",
            ])

    sortie = REFERENCE / f"equivalents_annonces_dzair{args.suffixe}.csv"
    with open(sortie, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(CHAMPS)
        writer.writerows(sorted(lignes))

    print(f"  {len(lignes)} équivalents annoncés -> {sortie.name}")
    print(f"  {len(vus_produits)} produits distincts")
    print()
    print(f"  interactions derrière le paywall du site : {paywall}")
    print("      « Réservé aux professionnels de santé. » Ce n'est pas une")
    print("      lacune de la collecte : le site réserve cette rubrique.")
    print(f"  fiches sans aucun équivalent listé : {sans_equivalent}")
    print(f"  fiches hors de notre périmètre     : {hors_perimetre}")
    print()
    print("  substitution indiquée par le site :")
    for valeur, n in substituables.most_common():
        print(f"      {n:>5}  {valeur}")
    print(f"  produits ayant une photo collectée : "
          f"{sum(1 for x in vus_produits if x in photos)}/{len(vus_produits)}")
    print()
    print("  RANG 1. Le site se prononce sur la substitution ; nos groupes")
    print("  d'équivalents s'y refusent, parce que c'est un jugement")
    print("  pharmaceutique. On enregistre donc ce qu'il dit, avec son rang,")
    print("  sans le reprendre à notre compte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
