"""Le corpus de la semaine 1 doit rester citable.

Ces tests ne vérifient pas que la recherche est bonne — c'est le rôle du jeu
d'évaluation. Ils vérifient qu'un passage produit ici respecte les règles du
projet : une provenance, une autorité juste, et des nombres recopiés tels quels
pour qu'une citation puisse être vérifiée mot pour mot.
"""

from __future__ import annotations

import pytest

from pharmeazor.retrieve.passages import (
    passages_equivalents,
    passages_interactions,
    passages_produits,
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
