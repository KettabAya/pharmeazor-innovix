"""Dosage and packaging parsing, on strings taken from the real nomenclature."""

import pytest

from pharmeazor.normalize.dosage import (
    normalize_unit,
    parse_packaging,
    parse_strength,
)


class TestUnits:
    def test_known_spellings_are_canonical(self):
        assert normalize_unit("MG") == "mg"
        assert normalize_unit("G") == "g"
        assert normalize_unit("ML") == "ml"

    def test_microgram_variants_agree(self):
        assert normalize_unit("MCG") == normalize_unit("UG") == "µg"

    def test_unknown_unit_passes_through(self):
        assert normalize_unit("DOSE") == "dose"

    def test_empty_unit_is_empty(self):
        assert normalize_unit(None) == ""


class TestSimpleStrength:
    def test_single_quantity(self):
        s = parse_strength("500MG")
        assert s.canonical() == "500mg"
        assert not s.is_combination
        assert s.parsed

    def test_gram(self):
        assert parse_strength("1G").canonical() == "1g"

    def test_french_decimal_comma(self):
        assert parse_strength("37,5MG").canonical() == "37.5mg"

    def test_une_fraction_nue_est_lue_comme_un_pourcentage(self):
        """Le registre ecrit « 0,03 » sans aucune unite : c'est une fraction.

        Revu le 19/11/2026. Ce test attendait « 0.03 », c'est-a-dire la valeur
        gardee telle quelle, sans unite. Mais une concentration sans unite ne
        veut rien dire pour un pharmacien, et surtout le registre ecrit la
        MEME chose des deux facons : le collyre diclofenac a 0,1 % est
        « 0,001 » pour VOLTARENE et XINAC, « 0.1% » pour DICLOGESIC. Les deux
        notations tombaient dans deux groupes d'equivalents distincts, et
        DICLOGESIC paraissait sans aucun equivalent alors qu'il en a deux.

        L'interpretation est verifiee six fois contre la concentration de
        reference : 0,001 collyre diclofenac = 0,1 %, 0,003 pommade
        ciprofloxacine = 0,3 %, 0,0075 gel metronidazole = 0,75 %, 0,01 gel
        diclofenac = 1 %, 0,025 gel ketoprofene = 2,5 %, 0,03 solution
        buvable paracetamol = 3 % soit 30 mg/ml.
        """
        s = parse_strength("0,03")
        assert s.parsed
        assert s.canonical() == "3%"

    def test_les_deux_notations_du_meme_dosage_se_rejoignent(self):
        assert parse_strength("0,001").canonical() == parse_strength("0.1%").canonical()

    def test_une_valeur_avec_unite_n_est_pas_touchee(self):
        """La regle ne vise QUE la fraction nue : « 0,5MG » reste 0,5 mg."""
        assert parse_strength("0,5MG").canonical() == "0.5mg"
        assert parse_strength("0,5G").canonical() == "0.5g"

    def test_raw_text_is_always_preserved(self):
        assert parse_strength("  500MG ").raw == "500MG"


class TestCombinations:
    def test_two_actives(self):
        s = parse_strength("325MG/37,5MG")
        assert s.is_combination
        assert s.canonical() == "325mg+37.5mg"

    def test_amoxicillin_clavulanate(self):
        assert parse_strength("1G/125MG").canonical() == "1g+125mg"

    def test_amlodipine_valsartan(self):
        assert parse_strength("5MG/160MG").canonical() == "5mg+160mg"

    def test_concentration_keeps_both_parts(self):
        s = parse_strength("250MG/5ML")
        assert [str(c) for c in s.components] == ["250mg", "5ml"]

    def test_ministry_footnote_asterisks_are_ignored(self):
        # "875MG*/125MG*" is amoxicillin + clavulanic acid; the stars are notes.
        s = parse_strength("875MG*/125MG*")
        assert s.canonical() == "875mg+125mg"
        assert s.raw == "875MG*/125MG*"

    def test_trailing_unit_is_recorded_not_dropped(self):
        s = parse_strength("100MG/12,5MG/ML")
        assert s.canonical() == "100mg+12.5mg"
        assert s.unparsed == ("ML",)


class TestUnparsableStrength:
    def test_text_only_is_not_invented(self):
        s = parse_strength("CF NOTICE")
        assert not s.parsed
        assert s.components == ()
        assert s.unparsed == ("CF NOTICE",)

    def test_empty_cell(self):
        s = parse_strength("")
        assert not s.parsed
        assert s.raw == ""

    def test_none_cell(self):
        assert not parse_strength(None).parsed


class TestPackaging:
    @pytest.mark.parametrize(
        "raw,expected",
        [("B/16", 16), ("B/10", 10), ("B/15", 15), ("B/20", 20), ("B/100", 100)],
    )
    def test_box_counts(self, raw, expected):
        assert parse_packaging(raw).count == expected

    def test_bottle_has_no_unit_count(self):
        # "B/FL 15 ML" is a 15 ml bottle, not 15 tablets. Returning 15 would lie.
        pack = parse_packaging("B/FL 15 ML")
        assert pack.count is None
        assert pack.container == "FL"
        assert str(pack.volume) == "15ml"

    def test_unrecognised_packaging_is_not_guessed(self):
        pack = parse_packaging("CONDITIONNEMENT HOSPITALIER")
        assert pack.count is None
        assert not pack.parsed
        assert pack.raw == "CONDITIONNEMENT HOSPITALIER"

    def test_empty_cell(self):
        assert not parse_packaging("").parsed

class TestConditionnementsMesures:
    """Les contenants dont le contenu se mesure au lieu de se compter.

    Mesure sur les 911 produits des 38 molecules : 163 conditionnements
    echappaient a la lecture sans etre des "ET". Deux familles dominaient,
    77 cas pour l'une et 34 pour l'autre ; la regle a ete ecrite d'apres cette
    distribution, et non d'apres quelques exemples.
    """

    @pytest.mark.parametrize("raw,valeur,contenant", [
        ("T/30G", "30g", "T"),
        ("TUBE/30G", "30g", "TUBE"),
        ("FL/30ML", "30ml", "FL"),
        ("FL/125 ML", "125ml", "FL"),
        ("FL./100ML", "100ml", "FL"),
        ("F/5ML", "5ml", "F"),
    ])
    def test_le_contenant_porte_sa_mesure(self, raw, valeur, contenant):
        pack = parse_packaging(raw)
        assert pack.parsed
        assert str(pack.volume) == valeur
        assert pack.container == contenant
        # Une mesure n'est pas un nombre d'unites : 30 g de pommade ne font
        # pas 30 comprimes.
        assert pack.count is None

    @pytest.mark.parametrize("raw,compte,valeur", [
        ("B/05 AMP. DE 2ML", 5, "2ml"),
        ("B/01 FL DE 60ML", 1, "60ml"),
        ("BOITE DE 01 FLACON DE 60ML", 1, "60ml"),
        ("B/10 AMP DE 1 ML", 10, "1ml"),
    ])
    def test_une_boite_de_n_contenants_porte_les_deux(self, raw, compte, valeur):
        """Cinq ampoules de 2 ml, ce n'est ni "cinq" ni "2 ml" : c'est les deux."""
        pack = parse_packaging(raw)
        assert pack.count == compte
        assert str(pack.volume) == valeur

    def test_deux_presentations_echouent_toujours(self):
        """Decision de la semaine 1, que l'elargissement ne doit pas defaire.

        "B/30 ET B/90" decrit deux tailles de boite dans une seule cellule.
        Choisir l'une des deux serait inventer.
        """
        for raw in ("B/30 ET B/90", "B/10 ET B/25"):
            assert not parse_packaging(raw).parsed

    def test_le_pilulier_trouve_a_la_main_marche_toujours(self):
        """Cas repere par une verification manuelle, pas par les tests."""
        assert parse_packaging("PILULIER/10").count == 10

