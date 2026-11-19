"""Tests du lecteur de classeurs du ministere.

Pourquoi ces tests existent
---------------------------
`collect/nomenclature.py` est la fondation de toute la chaine : si lui se
trompe, tout ce qui suit est faux sans que rien ne proteste. Or, au 19/11/2026,
aucun des 225 tests ne l'appelait -- parce qu'il faut un vrai fichier Excel
pour l'exercer, et qu'un fichier Excel est plus long a fabriquer qu'une chaine
de caracteres.

Les trois choses fragiles qu'il fait, et que ces tests verrouillent :

1. il **cherche** la ligne d'en-tete, qui est en ligne 14 dans les classeurs
   de version et en ligne 11 dans les classeurs annuels ;
2. il lit chaque cellule **par titre**, jamais par position -- la feuille
   « Retraits » n'a pas les memes colonnes ni le meme ordre ;
3. il distingue les trois feuilles.

Le classeur d'essai est fabrique ici meme, en memoire. Il imite les defauts du
vrai : en-tete precede d'un bloc a lettre, colonnes dans le desordre sur la
feuille des retraits, fautes de frappe et asterisques de bas de page conserves.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pharmeazor.collect.nomenclature import (  # noqa: E402
    find_header_row,
    read_workbook,
    sheet_kind,
)

openpyxl = pytest.importorskip("openpyxl")

# L'ordre des titres sur la feuille principale.
TITRES_NOMENCLATURE = [
    "N°", "N°ENREGISTREMENT", "CODE", "DENOMINATION COMMUNE INTERNATIONALE",
    "NOM DE MARQUE", "FORME", "DOSAGE", "CONDITIONNEMENT", "LISTE",
    "P1", "P2", "OBS",
    "LABORATOIRES DETENTEUR DE LA DECISION D'ENREGISTREMENT",
    "PAYS DU LABORATOIRE DETENTEUR DE LA DECISION D'ENREGISTREMENT",
    "DATE D'ENREGISTREMENT INITIAL", "DATE D'ENREGISTREMENT FINAL",
    "TYPE", "STATUT", "DUREE DE STABILITE",
]

# La feuille des retraits : pas de OBS, deux colonnes en plus, et surtout un
# ORDRE DIFFERENT. Une lecture par position mettrait la date dans le
# laboratoire -- c'est exactement le piege que ce fichier reproduit.
TITRES_RETRAITS = [
    "N°", "N°ENREGISTREMENT", "DATE DE RETRAIT", "MOTIF DE RETRAIT",
    "DENOMINATION COMMUNE INTERNATIONALE", "NOM DE MARQUE", "FORME", "DOSAGE",
    "CONDITIONNEMENT", "LISTE",
    "LABORATOIRES DETENTEUR DE LA DECISION D'ENREGISTREMENT",
    "PAYS DU LABORATOIRE DETENTEUR DE LA DECISION D'ENREGISTREMENT",
    "DATE D'ENREGISTREMENT INITIAL", "DATE D'ENREGISTREMENT FINAL",
    "TYPE", "STATUT", "DUREE DE STABILITE", "CODE",
]

LIGNES_NOMENCLATURE = [
    [1, "077/03 B 026/17", "03 B 026", "PARACETAMOL", "DOLIPRANE",
     "COMPRIME", "500MG", "B/20", "LISTE I", "", "", "",
     "LABORATOIRE ALGERIEN", "ALGERIE", "2017-03-01", "2027-03-01",
     "F", "F", "36 MOIS"],
    # Faute de frappe et asterisque de bas de page du vrai registre : ils
    # doivent ressortir INTACTS, la correction se fait plus loin dans la chaine.
    [2, "077/03 B 027/18", "03 B 027", "AMOXICILLINE TRIHYDRATEE", "CLAMOXYL",
     "POUDRE POUR SUSPENSSION BUVABLE", "875MG*", "B/12", "Liste I", "", "", "",
     "BIOPHARM", "ALGERIE", "2018-05-02", "2028-05-02", "I", "F", "24 MOIS"],
    # Ligne sans numero d'enregistrement : inutilisable, elle doit etre ecartee.
    [3, "", "", "IBUPROFENE", "SANS NUMERO", "COMPRIME", "400MG", "B/20",
     "", "", "", "", "LABO", "ALGERIE", "", "", "", "", ""],
]

LIGNES_RETRAITS = [
    [1, "077/03 B 099/11", "2011-05-08",
     "RETRAIT PAR LE MSPRH POUR INTERDICTION DE LA SUBSTANCE",
     "ACIDE ACETYLSALICYLIQUE", "ASPIRINE PH8", "COMPRIME", "500MG", "B/20",
     "", "LABORATOIRES PHARMA", "ALGERIE", "2001-01-01", "2011-05-08",
     "F", "R", "36 MOIS", "04 B 099"],
]

LIGNES_NON_RENOUVELES = [
    [1, "077/03 B 055/09", "03 B 055", "ACIDE ACETYLSALICYLIQUE",
     "ASPIRINE BEKER", "COMPRIME", "100MG", "B/30", "", "", "", "",
     "LABORATOIRES BEKER", "ALGERIE", "2009-02-01", "2019-02-01",
     "F", "N", "36 MOIS"],
]


def _ecrire_feuille(worksheet, titres: list[str], lignes: list[list]) -> None:
    """Un bloc a lettre d'abord, les titres en ligne 14, puis les donnees.

    Les treize premieres lignes ne portent qu'une seule cellule, comme le
    papier a en-tete du ministere. C'est ce qui oblige le lecteur a CHERCHER
    la ligne de titres au lieu de la supposer.
    """
    for numero in range(1, 14):
        worksheet.cell(row=numero, column=1, value="MINISTERE DE L'INDUSTRIE PHARMACEUTIQUE")
    for colonne, titre in enumerate(titres, start=1):
        worksheet.cell(row=14, column=colonne, value=titre)
    for decalage, ligne in enumerate(lignes):
        for colonne, valeur in enumerate(ligne, start=1):
            worksheet.cell(row=15 + decalage, column=colonne, value=valeur)


@pytest.fixture
def classeur(tmp_path: Path) -> Path:
    """Un classeur d'essai a trois feuilles, aux defauts du vrai."""
    livre = openpyxl.Workbook()
    principale = livre.active
    principale.title = "Nomenclature Aout 2026"
    _ecrire_feuille(principale, TITRES_NOMENCLATURE, LIGNES_NOMENCLATURE)

    # L'espace final du titre est celui du vrai classeur.
    _ecrire_feuille(livre.create_sheet("Non Renouvelés "),
                    TITRES_NOMENCLATURE, LIGNES_NON_RENOUVELES)
    _ecrire_feuille(livre.create_sheet("Retraits"),
                    TITRES_RETRAITS, LIGNES_RETRAITS)

    chemin = tmp_path / "nomenclature_2026-08.xlsx"
    livre.save(chemin)
    return chemin


class TestLEnTeteEstCherchee:
    """L'en-tete n'est pas a la meme ligne selon les classeurs."""

    def test_la_ligne_de_titres_est_trouvee_sous_le_bloc_a_lettre(self, classeur):
        livre = openpyxl.load_workbook(classeur, read_only=True)
        assert find_header_row(livre["Nomenclature Aout 2026"]) == 14
        livre.close()

    def test_un_classeur_sans_en_tete_le_dit_au_lieu_de_deviner(self, tmp_path):
        livre = openpyxl.Workbook()
        livre.active["A1"] = "une seule cellule, pas d'en-tete"
        chemin = tmp_path / "vide_2026-08.xlsx"
        livre.save(chemin)
        relu = openpyxl.load_workbook(chemin, read_only=True)
        with pytest.raises(ValueError, match="En-tête introuvable"):
            find_header_row(relu.active)
        relu.close()


class TestLesTroisFeuilles:
    """Chaque feuille est reconnue, et on peut n'en demander qu'une."""

    def test_chaque_titre_est_classe(self):
        assert sheet_kind("Nomenclature Aout 2026") == "nomenclature"
        assert sheet_kind("Non Renouvelés ") == "non_renouveles"
        assert sheet_kind("Retraits") == "retraits"

    def test_les_trois_feuilles_sont_lues_par_defaut(self, classeur):
        feuilles = {r.source_sheet for r in read_workbook(classeur)}
        assert feuilles == {"nomenclature", "non_renouveles", "retraits"}

    def test_on_peut_n_en_demander_qu_une(self, classeur):
        lignes = read_workbook(classeur, sheets={"nomenclature"})
        assert {r.source_sheet for r in lignes} == {"nomenclature"}
        assert len(lignes) == 2

    def test_la_version_vient_du_nom_de_fichier(self, classeur):
        assert {r.source_version for r in read_workbook(classeur)} == {"2026-08"}


class TestLaLectureSeFaitParTitre:
    """Le piege de la feuille Retraits : ses colonnes sont dans un autre ordre.

    Lue par position, la date de retrait tomberait dans le code et le motif
    dans la DCI. C'est le defaut que le cahier des charges du projet demandait
    de prevenir, et que rien ne verifiait jusqu'ici.
    """

    def test_le_laboratoire_est_un_laboratoire_et_non_une_date(self, classeur):
        retrait = next(r for r in read_workbook(classeur, sheets={"retraits"}))
        assert retrait.lab_name == "LABORATOIRES PHARMA"
        assert "-" not in retrait.lab_name

    def test_la_dci_est_une_substance_et_non_un_motif(self, classeur):
        retrait = next(r for r in read_workbook(classeur, sheets={"retraits"}))
        assert retrait.inn == "ACIDE ACETYLSALICYLIQUE"
        assert retrait.brand_name == "ASPIRINE PH8"

    def test_la_date_et_le_motif_de_retrait_sont_lus(self, classeur):
        retrait = next(r for r in read_workbook(classeur, sheets={"retraits"}))
        assert retrait.withdrawal_date == "2011-05-08"
        assert retrait.withdrawal_reason.startswith("RETRAIT PAR LE MSPRH")

    def test_la_feuille_principale_n_a_ni_date_ni_motif_de_retrait(self, classeur):
        produit = read_workbook(classeur, sheets={"nomenclature"})[0]
        assert produit.withdrawal_date == ""
        assert produit.withdrawal_reason == ""


class TestCeQuiEstLuEtCeQuiNeLEstPas:
    def test_toutes_les_colonnes_utiles_arrivent(self, classeur):
        produit = read_workbook(classeur, sheets={"nomenclature"})[0]
        assert produit.registration_no == "077/03 B 026/17"
        assert produit.code == "03 B 026"
        assert produit.inn == "PARACETAMOL"
        assert produit.brand_name == "DOLIPRANE"
        assert produit.form == "COMPRIME"
        assert produit.strength_raw == "500MG"
        assert produit.packaging_raw == "B/20"
        assert produit.list_class == "LISTE I"
        assert produit.lab_name == "LABORATOIRE ALGERIEN"
        assert produit.lab_country == "ALGERIE"
        assert produit.status == "F"
        assert produit.stability == "36 MOIS"

    def test_les_dates_ressortent_au_format_iso(self, classeur):
        produit = read_workbook(classeur, sheets={"nomenclature"})[0]
        assert produit.date_initial == "2017-03-01"
        assert produit.date_final == "2027-03-01"

    def test_une_ligne_sans_numero_d_enregistrement_est_ecartee(self, classeur):
        marques = {r.brand_name for r in read_workbook(classeur)}
        assert "SANS NUMERO" not in marques

    def test_les_fautes_du_registre_sont_conservees(self, classeur):
        """Le lecteur ne corrige rien : il rend ce que le ministere a ecrit.

        « SUSPENSSION » est une faute reelle du registre, « 875MG* » porte un
        appel de note. Les corriger ici rendrait impossible de retrouver la
        valeur citee dans le fichier d'origine, ce que la regle d'or du projet
        interdit.
        """
        produit = read_workbook(classeur, sheets={"nomenclature"})[1]
        assert produit.form == "POUDRE POUR SUSPENSSION BUVABLE"
        assert produit.strength_raw == "875MG*"

    def test_la_casse_de_la_colonne_liste_n_est_pas_touchee(self, classeur):
        """« Liste I » reste « Liste I » : l'uniformisation vient apres."""
        produit = read_workbook(classeur, sheets={"nomenclature"})[1]
        assert produit.list_class == "Liste I"
