"""The door to the week-1 tables. If this breaks, nothing downstream works."""

import pytest

from pharmeazor.registry import (
    conflicts_for,
    equivalents_of,
    get_drug,
    interactions_of,
    resolve_drug,
)

# MIBRAL is amlodipine. Chosen because it has aliases, interactions and an
# equivalence group, so one product exercises four of the five functions.
MIBRAL = "DZ-0338"


class TestResolveDrug:
    def test_brand_name_is_found(self):
        assert resolve_drug("MIBRAL") == MIBRAL

    def test_case_does_not_matter(self):
        assert resolve_drug("mibral") == resolve_drug("MIBRAL")

    def test_spaces_around_the_name_are_ignored(self):
        assert resolve_drug("  mibral  ") == MIBRAL

    def test_unknown_name_gives_none(self):
        assert resolve_drug("ZZZ-PAS-UN-MEDICAMENT") is None

    def test_empty_name_gives_none(self):
        assert resolve_drug("") is None
        assert resolve_drug(None) is None


class TestGetDrug:
    def test_returns_the_row(self):
        produit = get_drug(MIBRAL)
        assert produit is not None
        assert produit["brand_name"] == "MIBRAL"
        assert produit["drug_id"] == MIBRAL

    def test_carries_the_source_so_the_row_can_be_checked(self):
        produit = get_drug(MIBRAL)
        assert produit["source_sheet"] == "nomenclature"
        assert produit["registration_no"]

    def test_unknown_id_gives_none(self):
        assert get_drug("DZ-999999") is None


class TestInteractions:
    def test_finds_interactions(self):
        lignes = interactions_of(MIBRAL)
        assert lignes
        inn = get_drug(MIBRAL)["inn"]
        assert all(r["inn"] == inn or r["substance_cible"] == inn for r in lignes)

    def test_every_interaction_carries_its_level_and_source(self):
        for ligne in interactions_of(MIBRAL):
            assert ligne["niveau"]
            assert ligne["source_origine"]

    def test_unknown_id_gives_an_empty_list(self):
        assert interactions_of("DZ-999999") == []


class TestEquivalents:
    def test_the_product_is_in_its_own_group(self):
        groupe = equivalents_of(MIBRAL)
        assert MIBRAL in {r["drug_id"] for r in groupe}

    def test_the_whole_group_shares_one_id(self):
        groupe = equivalents_of(MIBRAL)
        assert len({r["group_id"] for r in groupe}) == 1

    def test_a_group_has_more_than_one_product(self):
        """A group of one would not be an equivalence."""
        assert len(equivalents_of(MIBRAL)) > 1

    def test_unknown_id_gives_an_empty_list(self):
        assert equivalents_of("DZ-999999") == []


class TestConflicts:
    def test_says_which_table_each_row_came_from(self):
        for ligne in conflicts_for(MIBRAL):
            assert ligne["table"] in {"conflits", "desaccords_versions"}

    def test_rows_match_the_registration_number(self):
        numero = get_drug(MIBRAL)["registration_no"]
        for ligne in conflicts_for(MIBRAL):
            assert ligne["n_enregistrement"] == numero

    def test_a_product_without_disagreement_gives_an_empty_list(self):
        assert conflicts_for("DZ-999999") == []


class TestTheChainHolds:
    def test_a_name_leads_all_the_way_to_the_equivalents(self):
        """What the assistant does: name -> id -> row -> equivalents."""
        drug_id = resolve_drug("MIBRAL")
        produit = get_drug(drug_id)
        groupe = equivalents_of(drug_id)
        assert produit["inn"]
        assert all(r["inn"] == produit["inn"] for r in groupe)

    @pytest.mark.parametrize("nom", ["MIBRAL", "mibral", " MIBRAL "])
    def test_the_same_product_however_it_is_written(self, nom):
        assert resolve_drug(nom) == MIBRAL
