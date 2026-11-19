"""Tests du lecteur des PDF de la base française.

Ces tests ne touchent AUCUN vrai PDF : 3 664 fichiers et 990 Mo ne sont pas
dans le dépôt, et une suite de tests qui dépend de données absentes de git ne
peut pas tourner chez quelqu'un d'autre. Ils portent donc sur ce qui se teste
sans fichier : la lecture du nom de fichier, le filtrage, la provenance, et
le découpage en passages.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_index import AVERTISSEMENT, decouper  # noqa: E402

from pharmeazor.collect.bdm import (  # noqa: E402
    BDM_SOURCE_ID,
    DocumentBDM,
    lire_nom_de_fichier,
    parcourir,
)
from pharmeazor.schemas import Authority  # noqa: E402


class TestLireLeNomDeFichier:
    """`paracétamol_rcp_61143618.pdf` porte trois informations."""

    def test_les_trois_parties_sont_lues(self):
        d = lire_nom_de_fichier(Path("x/paracétamol/paracétamol_rcp_61143618.pdf"))
        assert d is not None
        assert d.molecule == "paracétamol"
        assert d.type_document == "rcp"
        assert d.identifiant == "61143618"

    def test_le_type_a_deux_mots_est_lu_entier(self):
        """`fiche_info` et `bon_usage` contiennent un souligné : un découpage
        naïf sur « _ » les couperait en deux et perdrait le type."""
        for nom, attendu in (("codéine_fiche_info_123.pdf", "fiche_info"),
                             ("codéine_bon_usage_123.pdf", "bon_usage")):
            d = lire_nom_de_fichier(Path("x/codéine") / nom)
            assert d is not None and d.type_document == attendu

    def test_une_molecule_a_plusieurs_mots_reste_entiere(self):
        d = lire_nom_de_fichier(
            Path("x/acide clavulanique/acide clavulanique_notice_99.pdf"))
        assert d is not None and d.molecule == "acide clavulanique"

    def test_un_nom_hors_motif_n_est_pas_devine(self):
        """Un fichier qu'on ne sait pas nommer ne doit PAS entrer dans le
        corpus sous une molécule approximative."""
        assert lire_nom_de_fichier(Path("x/y/notice_sans_molecule.pdf")) is None
        assert lire_nom_de_fichier(Path("x/y/paracétamol_autre_12.pdf")) is None


class TestLaMoleculeSeCompare:
    """Les dossiers sont accentués en minuscules, notre périmètre ne l'est pas."""

    def test_les_accents_et_la_casse_sont_aplanis(self):
        d = DocumentBDM(Path("x.pdf"), "céfuroxime", "rcp", "1")
        assert d.molecule_normalisee == "CEFUROXIME"

    def test_un_nom_a_plusieurs_mots_garde_ses_espaces(self):
        d = DocumentBDM(Path("x.pdf"), "acide acétylsalicylique", "rcp", "1")
        assert d.molecule_normalisee == "ACIDE ACETYLSALICYLIQUE"


class TestLAutoriteEstEtrangere:
    """Le point qui décide de tout l'usage de cette source."""

    def test_le_rang_est_institutionnel_et_pas_plus(self, tmp_path):
        fichier = tmp_path / "paracétamol_rcp_1.pdf"
        fichier.write_bytes(b"%PDF-1.4")
        d = lire_nom_de_fichier(fichier)
        p = d.provenance()
        assert p.authority is Authority.INSTITUTIONAL
        assert int(p.authority) == 2
        assert p.country == "FR"
        assert p.source_id == BDM_SOURCE_ID

    def test_elle_ne_vaut_pas_la_nomenclature_algerienne(self):
        """Rang 2 contre rang 3 : une source étrangère complète, elle ne
        remplace pas. Si cette comparaison s'inversait, un RCP français
        pourrait écraser ce que le ministère algérien a enregistré."""
        assert Authority.INSTITUTIONAL < Authority.NOMENCLATURE
        assert Authority.INSTITUTIONAL < Authority.OFFICIAL


class TestLIntituleNommeLeMedicament:
    """Défaut mesuré le 19/11/2026.

    Les premiers passages ne portaient que le contenu de la rubrique. Une
    question sur la posologie du paracétamol ramenait alors un passage de
    codéine : aucun des deux ne nommait son médicament. Un passage voyage
    seul, il doit dire de quoi il parle.
    """

    TEXTE = (
        "Dernière mise à jour le 03/11/2026\n"
        "ACIDE ACETYLSALICYLIQUE BIOGARAN 75 mg, comprimé gastro-résistant\n"
        "1. DENOMINATION DU MEDICAMENT\n"
    )

    def test_la_ligne_de_titre_est_retenue(self):
        d = DocumentBDM(Path("x.pdf"), "acide acétylsalicylique", "rcp", "1",
                        texte=self.TEXTE)
        assert d.intitule.startswith("ACIDE ACETYLSALICYLIQUE BIOGARAN 75 mg")

    def test_la_date_de_mise_a_jour_n_est_pas_prise_pour_un_titre(self):
        d = DocumentBDM(Path("x.pdf"), "paracétamol", "rcp", "1",
                        texte=self.TEXTE)
        assert "mise à jour" not in d.intitule

    def test_sans_texte_on_retombe_sur_le_nom_de_dossier(self):
        """Il vaut mieux un nom approximatif que pas de nom du tout."""
        d = DocumentBDM(Path("x.pdf"), "tramadol", "rcp", "1", texte="")
        assert d.intitule == "tramadol"


class TestLeFiltrage:
    @staticmethod
    def _arborescence(racine: Path) -> None:
        for molecule, noms in {
            "paracétamol": ["paracétamol_rcp_1.pdf", "paracétamol_notice_1.pdf"],
            "ibuprofène": ["ibuprofène_rcp_2.pdf"],
            "nifédipine": ["nifédipine_rcp_3.pdf"],
        }.items():
            (racine / molecule).mkdir(parents=True)
            for nom in noms:
                (racine / molecule / nom).write_bytes(b"%PDF-1.4")

    def test_sans_filtre_tout_remonte(self, tmp_path):
        self._arborescence(tmp_path)
        assert len(list(parcourir(tmp_path))) == 4

    def test_le_filtre_par_type(self, tmp_path):
        self._arborescence(tmp_path)
        trouves = list(parcourir(tmp_path, types=("rcp",)))
        assert len(trouves) == 3
        assert {d.type_document for d in trouves} == {"rcp"}

    def test_le_filtre_par_molecule_ignore_les_accents(self, tmp_path):
        self._arborescence(tmp_path)
        trouves = list(parcourir(tmp_path, molecules=("IBUPROFENE",)))
        assert [d.molecule for d in trouves] == ["ibuprofène"]

    def test_une_molecule_hors_perimetre_est_ecartee(self, tmp_path):
        self._arborescence(tmp_path)
        assert list(parcourir(tmp_path, molecules=("AMOXICILLINE",))) == []


class TestLeDecoupageEnPassages:
    def test_un_texte_court_reste_entier(self):
        assert decouper("une phrase courte", 900, 150) == ["une phrase courte"]

    def test_un_texte_vide_ne_donne_aucun_passage(self):
        assert decouper("   ", 900, 150) == []

    def test_les_morceaux_se_chevauchent(self):
        """Sans recouvrement, une phrase coupee en deux n'existe entiere dans
        aucun morceau -- et une citation ne peut plus etre verifiee."""
        texte = " ".join(f"mot{i:03d}" for i in range(400))
        morceaux = decouper(texte, 200, 60)
        assert len(morceaux) > 1
        for avant, apres in zip(morceaux, morceaux[1:], strict=False):
            fin = avant[-40:]
            assert any(m in apres for m in fin.split()), "aucun chevauchement"

    def test_aucun_mot_n_est_coupe_en_deux(self):
        texte = " ".join(f"mot{i:03d}" for i in range(400))
        for morceau in decouper(texte, 200, 60):
            for mot in morceau.split():
                assert mot.startswith("mot") and len(mot) == 6, mot

    def test_le_texte_entier_est_couvert(self):
        texte = " ".join(f"mot{i:03d}" for i in range(400))
        vus = set()
        for morceau in decouper(texte, 200, 60):
            vus.update(morceau.split())
        assert vus == set(texte.split())


class TestLAvertissementEstPorteParLePassage:
    """La règle du cahier des charges, écrite dans le texte lui-même."""

    def test_il_dit_que_la_source_est_etrangere(self):
        assert "française" in AVERTISSEMENT

    def test_il_dit_qu_elle_complete_sans_remplacer(self):
        assert "complète" in AVERTISSEMENT
        assert "ne la remplace pas" in AVERTISSEMENT

    def test_il_previent_que_le_produit_peut_differer(self):
        assert "enregistré en France" in AVERTISSEMENT
        assert "peuvent différer" in AVERTISSEMENT


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1]
         / "data/raw/bdm/row-data/pdf/bdm_pdf").exists(),
    reason="les PDF collectés ne sont pas dans le dépôt",
)
def test_sur_les_vrais_fichiers_si_ils_sont_la():
    """Un garde-fou qui ne tourne que sur la machine qui a les PDF."""
    racine = (Path(__file__).resolve().parents[1]
              / "data/raw/bdm/row-data/pdf/bdm_pdf")
    documents = list(parcourir(racine))
    assert len(documents) > 3000
    assert {d.type_document for d in documents} == {
        "rcp", "notice", "fiche_info", "bon_usage"}
