"""Joining the two sources and reporting where they disagree."""

import datetime as dt
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from pharmeazor.normalize.catalogue import Product
from pharmeazor.normalize.dosage import parse_packaging, parse_strength
from pharmeazor.reconcile.crosscheck import (
    COMPARED_FIELDS,
    compare_all,
    compare_pair,
    join_on_registration,
    normalize_value,
)
from pharmeazor.schemas import Authority, Provenance

# `build_week1.py` est un script, pas un module installe : on l'importe par
# son chemin pour tester `conflits_de_retrait`, qui y vit.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_week1 import _sans_ponctuation, conflits_de_retrait  # noqa: E402


@dataclass
class FakeSecondary:
    """Stands in for a DzairProduct, without needing the real exports."""

    registration_no: str
    inn: str = "IBUPROFENE"
    brand_name: str = "BRUFEN"
    form: str = "COMPRIME PELLICULE"
    strength_raw: str = "400MG"
    packaging_raw: str = "B/20"
    lab_name: str = "LABO X"
    date_initial: str = "2015-03-01"

    def provenance(self) -> Provenance:
        return Provenance(
            source_id="dzair_pharma",
            url="https://www.dzair-pharma.net/x",
            authority=Authority.PROFESSIONAL,
            collected_at=dt.date(2026, 11, 12),
        )


def official(registration_no: str, **overrides) -> Product:
    values = {
        "inn": "IBUPROFENE",
        "brand_name": "BRUFEN",
        "form": "COMPRIME PELLICULE",
        "strength_raw": "400MG",
        "packaging_raw": "B/20",
        "lab_name": "LABO X",
        "date_initial": "2015-03-01",
    }
    values.update(overrides)
    return Product(
        drug_id="DZ-0001",
        therapeutic_class="antalgique_ains",
        inn=values["inn"],
        brand_name=values["brand_name"],
        code="04 B 042",
        registration_no=registration_no,
        form=values["form"],
        strength=parse_strength(values["strength_raw"]),
        packaging=parse_packaging(values["packaging_raw"]),
        lab_name=values["lab_name"],
        lab_country="ALGERIE",
        date_initial=values["date_initial"],
        date_final="",
        status="F",
        source_version="2026-06",
    )


class TestNormalizeValue:
    def test_accents_and_case_do_not_count_as_a_difference(self):
        assert normalize_value("Comprimé pelliculé") == normalize_value("COMPRIME PELLICULE")

    def test_spacing_and_punctuation_are_flattened(self):
        assert normalize_value(" B/20 ") == normalize_value("B 20")

    def test_empty_values_normalise_to_empty(self):
        assert normalize_value(None) == ""


class TestJoin:
    def test_matches_on_registration_number(self):
        pairs, only_o, only_s = join_on_registration(
            [official("503/03 B 061/16")], [FakeSecondary("503/03 B 061/16")]
        )
        assert len(pairs) == 1
        assert not only_o and not only_s

    def test_join_tolerates_punctuation_differences(self):
        pairs, _, _ = join_on_registration(
            [official("503/03 B 061/16")], [FakeSecondary("503 03 B 061 16")]
        )
        assert len(pairs) == 1

    def test_reports_products_present_in_only_one_source(self):
        pairs, only_o, only_s = join_on_registration([official("A/1")], [FakeSecondary("B/2")])
        assert not pairs
        assert len(only_o) == 1 and len(only_s) == 1


class TestComparison:
    def test_identical_products_produce_no_disagreement(self):
        pairs, _, _ = join_on_registration([official("A/1")], [FakeSecondary("A/1")])
        assert compare_pair(pairs[0]) == []

    def test_a_differing_field_is_reported(self):
        pairs, _, _ = join_on_registration(
            [official("A/1", lab_name="LABO X")],
            [FakeSecondary("A/1", lab_name="LABO Y")],
        )
        found = compare_pair(pairs[0])
        assert len(found) == 1
        assert found[0].field_name == "laboratoire"

    def test_the_official_value_is_retained(self):
        pairs, _, _ = join_on_registration(
            [official("A/1", strength_raw="400MG")],
            [FakeSecondary("A/1", strength_raw="600MG")],
        )
        disagreement = compare_pair(pairs[0])[0]
        assert disagreement.retained == "400MG"
        assert "400MG" in disagreement.reason_fr
        assert "600MG" in disagreement.reason_fr  # the losing value stays visible

    def test_the_reason_names_both_collection_dates(self):
        pairs, _, _ = join_on_registration(
            [official("A/1", lab_name="X")], [FakeSecondary("A/1", lab_name="Y")]
        )
        reason = compare_pair(pairs[0])[0].reason_fr
        assert "2026" in reason
        assert "mise à jour" in reason  # staleness is offered as an explanation

    def test_an_empty_value_is_a_gap_not_a_disagreement(self):
        pairs, _, _ = join_on_registration(
            [official("A/1", strength_raw="")], [FakeSecondary("A/1", strength_raw="400MG")]
        )
        assert compare_pair(pairs[0]) == []


class TestReport:
    def test_agreement_rate_is_one_when_everything_matches(self):
        report = compare_all([official("A/1")], [FakeSecondary("A/1")])
        assert report.agreement_rate == 1.0
        assert report.disagreements == []

    def test_agreement_rate_falls_with_disagreements(self):
        report = compare_all([official("A/1", lab_name="X")], [FakeSecondary("A/1", lab_name="Y")])
        assert report.agreement_rate == pytest.approx(1 - 1 / len(COMPARED_FIELDS))

    def test_by_field_counts_disagreements(self):
        report = compare_all(
            [official("A/1", lab_name="X", form="GELULE")],
            [FakeSecondary("A/1", lab_name="Y", form="COMPRIME")],
        )
        assert report.by_field() == {"forme": 1, "laboratoire": 1}

    def test_empty_inputs_do_not_divide_by_zero(self):
        assert compare_all([], []).agreement_rate == 0.0


class TestUnProduitRetireEncorePublie:
    """Le desaccord le plus grave possible entre deux sources.

    Constate le 19/11/2026 : les cinq produits que la reconciliation listait
    comme « seulement chez dzair-pharma » -- sans jamais dire pourquoi --
    figurent tous dans la feuille « Retraits » du classeur officiel. Le plus
    ancien, ALMIRAL, a ete retire en 2007 : dix-neuf ans.

    Ce n'etait donc pas une lacune de notre appariement, mais une source
    secondaire qui presente comme disponible ce que l'autorite a retire du
    marche. Il fallait lire les feuilles de retraits pour pouvoir le dire.
    """

    RETIRES = [
        {
            "registration_no": "178/04 B 004/99",
            "brand_name": "ALMIRAL",
            "withdrawal_date": "2011-05-08",
            "withdrawal_reason": "RETRAIT PAR LE MSPRH POUR INTERDICTION",
            "source_sheet": "retraits",
            "source_version": "2026-08",
        }
    ]

    def test_la_ponctuation_du_numero_n_empeche_pas_le_rapprochement(self):
        # Le ministere ecrit « 178/04 B 004/99 », dzair « 178 04 B 004 99 ».
        assert _sans_ponctuation("178/04 B 004/99") == _sans_ponctuation("178 04 B 004 99")

    def test_un_orphelin_dzair_devient_un_desaccord_documente(self):
        rapport = SimpleNamespace(secondary_only=["178 04 B 004 99"])
        lignes = conflits_de_retrait(rapport, self.RETIRES)
        assert len(lignes) == 1
        ligne = lignes[0]
        assert ligne[1] == "statut d'enregistrement"
        assert "2011-05-08" in ligne[2]
        assert "RETRAIT PAR LE MSPRH" in ligne[2]
        assert ligne[3] == "publie comme enregistre"
        assert "nomenclature nationale fait foi" in ligne[9]

    def test_un_orphelin_qui_n_est_pas_retire_reste_inexplique(self):
        """On n'invente pas une explication pour un produit qu'on ne trouve pas."""
        rapport = SimpleNamespace(secondary_only=["999 99 Z 999 99"])
        assert conflits_de_retrait(rapport, self.RETIRES) == []
