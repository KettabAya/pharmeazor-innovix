"""Le corpus de la semaine 1 doit rester citable.

Ces tests ne vérifient pas que la recherche est bonne — c'est le rôle du jeu
d'évaluation. Ils vérifient qu'un passage produit ici respecte les règles du
projet : une provenance, une autorité juste, et des nombres recopiés tels quels
pour qu'une citation puisse être vérifiée mot pour mot.
"""

from __future__ import annotations

import pytest

from pharmeazor.retrieve.build_passages import (
    passages_equivalents,
    passages_interactions,
    passages_produits,
    passages_retraits,
)
from pharmeazor.schemas import Authority, Citation

LIGNE_PRODUIT = {
    "drug_id": "D001",
    "therapeutic_class": "ANALGESIQUE",
    "inn": "PARACETAMOL",
    "brand_name": "DOLIPRANE",
    "code": "03 B 005",
    "registration_no": "318/03 B 005/16/23",
    "form": "COMPRIME",
    "strength_raw": "500MG",
    "packaging_raw": "B/16",
    "list_class": "LISTE I",
    "lab_name": "PHARMIDAL NS",
    "lab_country": "ALGERIE",
    "date_initial": "2016-05-12",
    "date_final": "2023-05-12",
    "type_code": "G",
    "status": "Enregistre",
    "source_version": "2026-08",
    "source_sheet": "Feuil1",
}


def _produit(**remplacements):
    ligne = {**LIGNE_PRODUIT, **remplacements}
    return next(iter(passages_produits([ligne])))


def test_un_produit_porte_sa_provenance():
    p = _produit()
    assert p.provenance.source_id == "nomenclature"
    assert p.provenance.authority is Authority.NOMENCLATURE
    assert p.provenance.collected_at.year == 2026
    assert p.provenance.collected_at.month == 8


def test_la_nomenclature_ne_vaut_pas_un_rcp():
    """Rang 3, jamais 4 : elle dit ce qui est enregistre, pas la posologie."""
    p = _produit()
    assert p.provenance.authority < Authority.OFFICIAL


def test_le_dosage_est_recopie_tel_quel():
    """Si le dosage etait reformate, number_guard ne le retrouverait plus."""
    p = _produit(strength_raw="875MG*/125MG*")
    assert "875MG*/125MG*" in p.text


def test_un_champ_vide_ne_produit_pas_de_phrase():
    """Mieux vaut un silence qu'un « dosage : inconnu » invente."""
    p = _produit(strength_raw="", packaging_raw="")
    assert "dosage" not in p.text.lower()
    assert "conditionnement" not in p.text.lower()
    assert "DOLIPRANE" in p.text


def test_une_citation_du_passage_est_acceptee():
    p = _produit()
    citation = Citation(passage=p, quote="Son dosage est 500MG.")
    assert citation.quote in p.text


def test_une_citation_inventee_est_refusee():
    """La regle d'or : rien ne s'affiche sans source verifiable."""
    p = _produit()
    with pytest.raises(ValueError):
        Citation(passage=p, quote="Son dosage est 999MG.")


def test_un_groupe_d_un_seul_produit_est_ignore():
    """Un « equivalent » unique n'apprend rien au pharmacien."""
    ligne = {
        "group_id": "G1", "inn": "PARACETAMOL", "strength": "500MG",
        "form_family": "ORAL SEC", "group_size": "1", "drug_id": "D001",
        "brand_name": "DOLIPRANE", "form": "COMPRIME", "packaging": "B/16",
        "lab_name": "PHARMIDAL", "registration_no": "318/03", "status": "Enregistre",
    }
    assert list(passages_equivalents([ligne])) == []


def test_un_groupe_de_deux_produits_les_nomme_tous():
    base = {
        "group_id": "G1", "inn": "PARACETAMOL", "strength": "500MG",
        "form_family": "ORAL SEC", "group_size": "2", "form": "COMPRIME",
        "packaging": "B/16", "registration_no": "318/03", "status": "Enregistre",
    }
    lignes = [
        {**base, "drug_id": "D001", "brand_name": "DOLIPRANE", "lab_name": "A"},
        {**base, "drug_id": "D002", "brand_name": "EFFERALGAN", "lab_name": "B"},
    ]
    p = next(iter(passages_equivalents(lignes)))
    assert "DOLIPRANE" in p.text
    assert "EFFERALGAN" in p.text


def test_le_passage_equivalents_avertit_du_piege():
    """Meme substance et meme dosage ne veut pas dire interchangeable."""
    base = {
        "group_id": "G1", "inn": "PARACETAMOL", "strength": "500MG",
        "form_family": "ORAL SEC", "group_size": "2", "form": "COMPRIME",
        "packaging": "B/16", "registration_no": "318/03", "status": "Enregistre",
    }
    lignes = [
        {**base, "drug_id": "D001", "brand_name": "DOLIPRANE", "lab_name": "A"},
        {**base, "drug_id": "D002", "brand_name": "EFFERALGAN", "lab_name": "B"},
    ]
    p = next(iter(passages_equivalents(lignes)))
    assert "interchangeabilité" in p.text


def test_une_interaction_relayee_retombe_au_rang_secondaire():
    """Le contenu vient de l'ANSM, mais un relais peut introduire une erreur."""
    ligne = {
        "inn": "PARACETAMOL", "brand_name": "DOLIPRANE",
        "registration_no": "318/03", "substance_cible": "ANTIVITAMINES K",
        "type_cible": "Substance", "niveau": "Precaution d'emploi",
        "niveau_reconnu": "oui", "risques": "Risque hemorragique.",
        "conduite_a_tenir": "Controle de l'INR.", "source_origine": "ANSM",
        "source_relais": "dzair-pharma", "autorite_effective": "Secondaire",
        "url": "https://www.dzair-pharma.net/medicament/1",
    }
    p = next(iter(passages_interactions([ligne])))
    assert p.provenance.authority is Authority.PROFESSIONAL
    assert "ANSM" in p.text
    assert "confirmer" in p.text


def test_une_interaction_sans_cible_est_ignoree():
    ligne = {
        "inn": "PARACETAMOL", "brand_name": "", "registration_no": "",
        "substance_cible": "", "type_cible": "", "niveau": "",
        "niveau_reconnu": "", "risques": "", "conduite_a_tenir": "",
        "source_origine": "", "source_relais": "", "autorite_effective": "",
        "url": "",
    }
    assert list(passages_interactions([ligne])) == []


LIGNE_RETRAIT = {
    "registration_no": "053/03 A 001/97",
    "inn": "ACIDE ACETYLSALICYLIQUE",
    "brand_name": "ASPIRINE PH8",
    "form": "COMP.GASTRORESIST.",
    "strength_raw": "500MG",
    "packaging_raw": "B/30",
    "lab_name": "3M SANTE",
    "date_initial": "1997-01-01",
    "date_final": "2011-05-08",
    "withdrawal_date": "2011-05-08",
    "withdrawal_reason": "RETRAIT PAR LE MSPRH POUR INTERDICTION D'IMPORTATION",
    "source_version": "2026-08",
    "source_sheet": "retraits",
}


class TestLesProduitsSortisDuMarche:
    """Un produit retire doit pouvoir etre RECONNU, jamais PROPOSE.

    Ces passages existent pour que « c'est quoi, ASPIRINE PH8 ? » obtienne une
    reponse datee et sourcee, au lieu d'un silence qui se lit « je ne sais
    pas ». Ils ne doivent pour autant jamais ressembler a une offre.
    """

    def test_le_passage_dit_d_abord_que_le_produit_n_est_plus_enregistre(self):
        p = next(passages_retraits([LIGNE_RETRAIT]))
        assert p.text.startswith("ASPIRINE PH8 N'EST PLUS")

    def test_la_date_et_le_motif_sont_recopies_tels_quels(self):
        p = next(passages_retraits([LIGNE_RETRAIT]))
        assert "2011-05-08" in p.text
        assert "RETRAIT PAR LE MSPRH POUR INTERDICTION D'IMPORTATION" in p.text

    def test_le_passage_interdit_explicitement_de_le_delivrer(self):
        p = next(passages_retraits([LIGNE_RETRAIT]))
        assert "ne doit pas être délivré" in p.text
        assert "ne peut pas servir d'équivalent" in p.text

    def test_un_enregistrement_non_renouvele_se_dit_autrement_qu_un_retrait(self):
        ligne = dict(LIGNE_RETRAIT, source_sheet="non_renouveles",
                     withdrawal_date="", withdrawal_reason="")
        p = next(passages_retraits([ligne]))
        assert "n'a pas été renouvelé" in p.text
        assert "N'EST PLUS" not in p.text

    def test_l_autorite_reste_celle_de_la_nomenclature(self):
        p = next(passages_retraits([LIGNE_RETRAIT]))
        assert p.provenance.authority is Authority.NOMENCLATURE
        assert p.section == "retrait"

    def test_un_champ_vide_ne_produit_aucune_phrase(self):
        ligne = dict(LIGNE_RETRAIT, withdrawal_date="", withdrawal_reason="",
                     lab_name="", form="")
        p = next(passages_retraits([ligne]))
        assert "retiré le ." not in p.text
        assert "Motif" not in p.text
        assert "produit par" not in p.text

    def test_les_nombres_restent_citables_mot_pour_mot(self):
        p = next(passages_retraits([LIGNE_RETRAIT]))
        citation = Citation(passage=p, quote="Son dosage était 500MG.")
        assert citation.quote in p.text
        with pytest.raises(ValueError):
            Citation(passage=p, quote="Son dosage était 999MG.")

    def test_deux_produits_de_meme_numero_gardent_des_identifiants_distincts(self):
        jumeau = dict(LIGNE_RETRAIT, brand_name="ASPIRINE PH8 BIS")
        passages = list(passages_retraits([LIGNE_RETRAIT, jumeau]))
        assert len({p.passage_id for p in passages}) == 2


class TestLeCodeDeStatutNEstPasPresenteCommeCompris:
    """Le registre porte une lettre, F ou I, dont la legende n'est publiee
    nulle part.

    Mesure du 19/11/2026 : F accompagne 793 laboratoires algeriens contre 3
    etrangers, ce qui suggere « fabrique » contre « importe ». Mais 50
    produits ne rentrent pas dans l'hypothese -- TAREG, de Novartis Suisse,
    est marque F. Une correlation n'est pas une legende : le passage donne
    donc le code ET dit qu'il n'est pas documente.
    """

    def test_le_code_est_donne_avec_sa_reserve(self):
        p = next(passages_produits([LIGNE_PRODUIT]))
        assert "code de statut" in p.text
        assert "n'est publiée nulle part" in p.text

    def test_le_code_n_est_pas_presente_comme_une_information_comprise(self):
        p = next(passages_produits([LIGNE_PRODUIT]))
        assert "Son statut est" not in p.text


class TestLeGroupeNommeCeQuiDiffere:
    """Un groupe d'equivalents n'est pas toujours homogene.

    Mesure du 19/11/2026 sur les 153 groupes : 4 melangent un trait galenique
    (gastro-resistant, effervescent, orodispersible, liberation prolongee) et
    12 melangent le classement reglementaire. L'avertissement general
    « excipients et biodisponibilite peuvent differer » ne suffit pas : un
    pharmacien n'arbitre pas sur « peuvent differer », il arbitre sur
    « l'un est gastro-resistant, l'autre non ».
    """

    @staticmethod
    def _groupe(ecarts: str) -> list[dict]:
        base = {
            "group_id": "EQ-0012", "inn": "DICLOFENAC SODIQUE",
            "strength": "50mg", "form_family": "COMPRIME", "group_size": "2",
            "differences_dans_le_groupe": ecarts, "lab_name": "LABO",
        }
        return [dict(base, drug_id="D1", brand_name="VOLTARENE"),
                dict(base, drug_id="D2", brand_name="DICLOGESIC")]

    def test_l_ecart_est_nomme_quand_il_existe(self):
        p = next(passages_equivalents(self._groupe("gastro-résistant")))
        assert "n'est pas homogène sur : gastro-résistant" in p.text
        assert "La décision revient au pharmacien." in p.text

    def test_aucune_phrase_en_trop_quand_le_groupe_est_homogene(self):
        p = next(passages_equivalents(self._groupe("")))
        assert "homogène" not in p.text

    def test_l_avertissement_general_reste_present_dans_les_deux_cas(self):
        for ecarts in ("", "effervescent"):
            p = next(passages_equivalents(self._groupe(ecarts)))
            assert "ne vaut pas interchangeabilité clinique" in p.text


class TestUneInteractionConcerneUneSubstance:
    """Nommer une marque sur une interaction est faux par omission.

    Mesure du 19/11/2026 : les 16 interactions du diclofenac sodique
    nommaient BIOFENAC, alors que 36 marques du catalogue portent cette
    substance. Le passage disait « Medicament concerne : BIOFENAC », ce qui
    laisse entendre que les 35 autres ne le sont pas.
    """

    LIGNE = {
        "inn": "DICLOFENAC SODIQUE", "brand_name": "BIOFENAC",
        "registration_no": "263/04 B 007", "substance_cible": "MIFAMURTIDE",
        "type_cible": "substance", "niveau": "Contre-indication",
        "niveau_reconnu": "oui", "risques": "Risque de moindre efficacité.",
        "conduite_a_tenir": "Aucune conduite spécifique.",
        "source_origine": "ANSM", "source_relais": "dzair_pharma",
        "autorite_effective": "Professionnelle", "url": "https://example.test/x",
    }

    def test_la_substance_est_nommee_et_l_extension_dite(self):
        p = next(passages_interactions([self.LIGNE]))
        assert "concerne la substance DICLOFENAC SODIQUE" in p.text
        assert "TOUS les médicaments qui la contiennent" in p.text

    def test_la_marque_n_est_plus_presentee_comme_le_medicament_concerne(self):
        p = next(passages_interactions([self.LIGNE]))
        assert "Médicament concerné" not in p.text

    def test_la_marque_reste_citee_comme_provenance(self):
        """On ne perd pas l'information : elle dit d'ou la fiche a ete lue."""
        p = next(passages_interactions([self.LIGNE]))
        assert "Fiche d'où l'information a été lue : BIOFENAC." in p.text


class TestUnDosageEnFractionEstExplique:
    """« Son dosage est 0,001 » ne veut rien dire pour un pharmacien."""

    LIGNE = dict(LIGNE_PRODUIT, strength_raw="0,0075", brand_name="ROZEX")

    def test_la_valeur_brute_est_conservee_mot_pour_mot(self):
        p = next(passages_produits([self.LIGNE]))
        assert "Son dosage est 0,0075." in p.text

    def test_la_conversion_est_donnee(self):
        p = next(passages_produits([self.LIGNE]))
        assert "0,75 %" in p.text

    def test_la_conversion_est_attribuee_a_notre_lecture(self):
        """Le registre n'ecrit pas « 0,75 % ». Le passage doit le dire, sinon
        la phrase attribue au ministere un nombre qu'il n'a pas ecrit."""
        p = next(passages_produits([self.LIGNE]))
        assert "notre lecture" in p.text
        assert "n'est pas écrite dans le registre" in p.text

    def test_un_dosage_normal_ne_declenche_aucune_explication(self):
        p = next(passages_produits([LIGNE_PRODUIT]))
        assert "fraction" not in p.text
