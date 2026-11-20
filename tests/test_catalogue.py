"""The catalogue, the name dictionary and the equivalence rule."""

from pathlib import Path

import pytest

from pharmeazor.normalize.catalogue import Catalogue, form_family

CSV = Path(__file__).resolve().parents[1] / "data" / "reference" / "drugs_semaine1.csv"

pytestmark = pytest.mark.skipif(not CSV.exists(), reason="drugs_semaine1.csv not extracted yet")


@pytest.fixture(scope="module")
def catalogue() -> Catalogue:
    return Catalogue.from_csv(CSV)


class TestFormFamily:
    def test_coating_and_score_do_not_change_the_family(self):
        assert form_family("COMPRIME PELLICULE SECABLE") == "COMPRIME"
        assert form_family("COMPRIME") == "COMPRIME"

    def test_la_faute_du_registre_ne_change_pas_la_famille(self):
        """Le ministere ecrit tantot SUSPENSION, tantot SUSPENSSION.

        Ce test exigeait POUDRE pour la forme fautive, ce qui figeait un
        defaut : l'orthographe juste donnait SUSPENSION, et les deux
        ecritures du meme produit tombaient dans deux familles. Mesure du
        17/11/2026 : 17 produits fautifs contre 51 corrects, et
        AMOXICILLINE TRIHYDRATEE 1G/SACHET coupe en deux groupes pour cette
        seule raison.
        """
        assert form_family("POUDRE POUR SUSPENSSION BUVABLE") == "SUSPENSION"
        assert form_family("POUDRE POUR SUSPENSION BUVABLE") == "SUSPENSION"

    def test_capsule_family(self):
        assert form_family("GELULE") == "GELULE"

    def test_empty_form(self):
        assert form_family("") == ""


class TestLaVoiePrimeSurLaForme:
    """Une solution qu'on pique n'est pas une solution qu'on boit.

    Defaut mesure le 17/11/2026 sur les 911 produits : form_family rendait
    la premiere famille trouvee dans une liste unique, ou SOLUTION precedait
    INJECTABLE. 46 injectables et 15 collyres etaient donc ranges avec les
    solutions buvables, et un groupe d'equivalents etait deja faux :

        LEVOFLOXACINE 5 mg
          LEVOFLOXACINE RAZES  SOLUTION POUR PERFUSION
          LEVOQUIN             SOLUTION POUR PERFUSION
          LEVOWORLD            GOUTTES OCULAIRES ET AURICULAIRES

    Des gouttes pour les yeux proposees comme remplacant d'une perfusion.
    """

    @pytest.mark.parametrize(
        "forme,famille",
        [
            ("SOLUTION INJECTABLE IM/IV", "INJECTABLE"),
            ("SOLUTION INJECTABLE", "INJECTABLE"),
            ("POUDRE POUR SOLUTION INJECTABLE IV", "INJECTABLE"),
            ("SOLUTION POUR PERFUSION", "PERFUSION"),
            ("COLLYRE EN SOLUTION", "COLLYRE"),
            ("GOUTTES OCULAIRES ET AURICULAIRES EN SOLUTION", "OCULAIRE"),
            ("SOL AURICULAIRE STERILE", "AURICULAIRE"),
            ("OVULE VAGINALE", "VAGINAL"),
            ("COMPRIME VAGINAL", "VAGINAL"),
        ],
    )
    def test_une_voie_citee_l_emporte(self, forme, famille):
        assert form_family(forme) == famille

    def test_une_forme_sans_voie_citee_n_est_pas_touchee(self):
        """La correction ne doit pas emporter les formes ordinaires."""
        assert form_family("SOLUTION BUVABLE") == "SOLUTION"
        assert form_family("COMPRIME PELLICULE") == "COMPRIME"
        # "POUDRE POUR X" rend X : ce qui compte est la forme administree,
        # pas celle de la boite. Une poudre pour solution buvable se boit.
        assert form_family("POUDRE POUR SOLUTION BUVABLE") == "SOLUTION"

    def test_le_cas_levoworld_ne_peut_plus_se_reproduire(self):
        perfusion = form_family("SOLUTION POUR PERFUSION")
        gouttes = form_family("GOUTTES OCULAIRES ET AURICULAIRES EN SOLUTION")
        assert perfusion != gouttes

    def test_injectable_et_buvable_ne_se_rejoignent_jamais(self):
        assert form_family("SOLUTION INJECTABLE IM") != form_family("SOLUTION BUVABLE")


class TestLoading:
    def test_loads_every_row(self, catalogue):
        # Derived from the file rather than hardcoded, so changing which
        # molecules are extracted does not break the test.
        import csv as _csv

        with open(CSV, encoding="utf-8", newline="") as fh:
            expected = sum(1 for _ in _csv.DictReader(fh))
        assert len(catalogue.products) == expected
        assert expected > 50

    def test_every_product_has_a_therapeutic_class(self, catalogue):
        """Aucune classe inventee, et aucune case vide.

        Le vocabulaire a ete affine le 19/11/2026. « antalgique_ains »
        melangeait deux choses : le paracetamol est antalgique mais n'est PAS
        anti-inflammatoire, et le confondre avec un AINS laisserait croire
        qu'il en partage les contre-indications digestives et renales. Les
        diuretiques et les betabloquants, de meme, abaissent la tension sans
        rien partager de leurs effets indesirables.
        """
        classes = {p.therapeutic_class for p in catalogue.products}
        assert classes
        assert "" not in classes
        assert classes <= {
            "antalgique",
            "ains",
            "antibiotique",
            "antihypertenseur",
            "diuretique",
            "betabloquant",
        }

    def test_le_paracetamol_n_est_pas_range_avec_les_ains(self, catalogue):
        """Defaut corrige le 19/11/2026 : il l'etait depuis la semaine 1."""
        paracetamols = [p for p in catalogue.products if p.inn.upper().startswith("PARACETAMOL")]
        assert paracetamols, "le jeu de test ne contient aucun paracetamol"
        assert {p.therapeutic_class for p in paracetamols} == {"antalgique"}

    def test_strengths_were_parsed_for_the_vast_majority(self, catalogue):
        parsed = sum(1 for p in catalogue.products if p.strength.parsed)
        assert parsed / len(catalogue.products) > 0.95

    def test_every_product_can_cite_its_source(self, catalogue):
        prov = catalogue.products[0].provenance()
        assert "nomenclature" in prov.source_id
        assert "2026" in prov.cite()


class TestNameIndex:
    def test_brand_name_resolves(self, catalogue):
        assert catalogue.find_by_name("EFFERALGAN")

    def test_inn_resolves_to_many_products(self, catalogue):
        assert len(catalogue.find_by_name("PARACETAMOL")) > 50

    def test_lookup_ignores_case_and_accents(self, catalogue):
        assert catalogue.find_by_name("efferalgan") == catalogue.find_by_name("EFFERALGAN")

    def test_unknown_name_returns_nothing(self, catalogue):
        assert catalogue.find_by_name("ZZZ-INEXISTANT") == []

    def test_aliases_cover_all_four_kinds(self, catalogue):
        kinds = {a.kind for a in catalogue.aliases()}
        assert kinds == {"brand", "inn", "code", "registration"}

    def test_drug_entries_feed_the_resolver(self, catalogue):
        from pharmeazor.normalize.names import NameResolver

        entries = catalogue.drug_entries()
        assert len(entries) == len(catalogue.products)
        # A typo on a brand name must still reach a product.
        result = NameResolver(entries[:60]).resolve("EFERALGAN")
        assert result is not None


class TestEquivalence:
    def test_products_group_by_substance_strength_and_form(self, catalogue):
        groups = catalogue.groups()
        assert groups
        biggest = groups[0]
        assert biggest.size > 1
        assert len({p.inn for p in biggest.products}) == 1
        assert len({p.strength.canonical() for p in biggest.products}) == 1

    def test_a_tablet_never_groups_with_a_syrup(self, catalogue):
        for group in catalogue.groups():
            assert len({p.form_family for p in group.products}) == 1

    def test_products_without_a_readable_strength_are_excluded(self, catalogue):
        grouped = {p.drug_id for g in catalogue.groups() for p in g.products}
        for product in catalogue.products:
            if not product.strength.parsed:
                assert product.drug_id not in grouped


class TestEquivalentsAnswer:
    def test_unknown_name_is_refused_not_guessed(self, catalogue):
        answer = catalogue.equivalents_of("ZZZ-INEXISTANT")
        assert answer["refused"]
        assert answer["citations"] == []

    def test_ambiguous_name_asks_instead_of_choosing(self, catalogue):
        # A brand sold in several strengths must not be resolved silently.
        ambiguous = None
        for product in catalogue.products:
            same = catalogue.find_by_name(product.brand_name)
            if len({m.equivalence_key for m in same}) > 1:
                ambiguous = product.brand_name
                break
        if ambiguous is None:
            pytest.skip("no ambiguous brand in this extract")
        answer = catalogue.equivalents_of(ambiguous)
        assert answer["refused"]
        assert "Précisez" in answer["limits"]

    def test_a_resolved_answer_carries_a_citation_per_product(self, catalogue):
        answer = None
        for group in catalogue.groups():
            if group.size < 2:
                continue
            candidate = group.products[0]
            trial = catalogue.equivalents_of(candidate.brand_name)
            if not trial["refused"]:
                answer = trial
                break
        assert answer is not None, "expected at least one unambiguous product"
        assert answer["equivalents"]
        assert len(answer["citations"]) == len(answer["equivalents"]) + 1
        assert all(c["registration_no"] for c in answer["citations"])

    def test_answer_states_its_limits(self, catalogue):
        for group in catalogue.groups():
            trial = catalogue.equivalents_of(group.products[0].brand_name)
            if not trial["refused"]:
                assert "posologie" in trial["limits"]
                return
        pytest.skip("no unambiguous product found")
