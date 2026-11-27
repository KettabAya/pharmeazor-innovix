"""The five guards. One test file, so nobody has to look in two places."""

import datetime as _dt

import pytest

from pharmeazor.answer import checks
from pharmeazor.answer.checks import (
    Verdict,
    check_budget,
    check_numbers,
    check_out_of_scope,
    check_patient_context,
    check_sources_present,
    run_all,
)
from pharmeazor.schemas import Authority, Citation, Passage, Provenance

PASSAGE_TEXTE = (
    "La posologie usuelle est de 500 mg par prise, sans dépasser 3 g par 24 h. "
    "Respecter un intervalle minimal de 4 heures entre les prises."
)


def _citation(quote: str = "500 mg par prise") -> Citation:
    """One real citation, so the guards get the shape they expect."""
    provenance = Provenance(
        source_id="anpp_rcp",
        url="https://rcp.anpp.dz/exemple",
        authority=Authority.OFFICIAL,
        collected_at=_dt.date(2026, 11, 17),
    )
    passage = Passage(
        passage_id="p1",
        doc_id="paracetamol_rcp",
        text=PASSAGE_TEXTE,
        provenance=provenance,
        section="posologie",
    )
    return Citation(passage=passage, quote=quote)


class TestCitation:
    def test_a_quote_that_is_not_in_the_passage_cannot_be_built(self):
        """This is the golden rule, enforced by the schema itself."""
        with pytest.raises(ValueError):
            _citation("la dose est de 10 g")


class TestNumbers:
    def test_right_number_passes(self):
        result = check_numbers("La posologie est de 500 mg par prise.", [_citation()])
        assert result.verdict is Verdict.PASS

    def test_wrong_number_is_blocked(self):
        result = check_numbers("La posologie est de 900 mg par prise.", [_citation()])
        assert result.verdict is Verdict.BLOCK
        assert "900" in result.reason

    def test_spelled_out_dose_is_checked_too(self):
        """ "quatre grammes" must not slip through just because it has no digit."""
        result = check_numbers("Ne pas dépasser quatre grammes par jour.", [_citation()])
        assert result.verdict is Verdict.BLOCK

    def test_counting_words_are_not_doses(self):
        """Blocked a correct answer on 27/11/2026: "entre deux prises" -> "2 prise"."""
        result = check_numbers("Attendre au moins 4 heures entre deux prises.", [_citation()])
        assert result.verdict is Verdict.PASS


class TestSources:
    def test_no_citation_is_blocked(self):
        result = check_sources_present("La posologie est de 500 mg.", [])
        assert result.verdict is Verdict.BLOCK

    def test_a_refusal_needs_no_source(self):
        result = check_sources_present("Je n'ai pas cette donnée.", [], est_un_refus=True)
        assert result.verdict is Verdict.PASS

    def test_citation_present_passes(self):
        result = check_sources_present("La posologie est de 500 mg.", [_citation()])
        assert result.verdict is Verdict.PASS


class TestScope:
    def test_price_question_is_blocked(self):
        """The field is empty on all 1 650 products, but BM25 scores it 8.98."""
        result = check_out_of_scope("Quel est le prix du DOLIPRANE en Algérie ?")
        assert result.verdict is Verdict.BLOCK
        assert "prix" in result.reason

    def test_stock_question_is_blocked(self):
        result = check_out_of_scope("Est-il disponible en pharmacie à Constantine ?")
        assert result.verdict is Verdict.BLOCK

    def test_posology_question_passes(self):
        result = check_out_of_scope("Quelle est la posologie du paracétamol ?")
        assert result.verdict is Verdict.PASS

    def test_accents_do_not_matter(self):
        assert check_out_of_scope("quel est le cout ?").verdict is Verdict.BLOCK
        assert check_out_of_scope("quel est le coût ?").verdict is Verdict.BLOCK


class TestPatientContext:
    def test_personal_question_is_blocked(self):
        result = check_patient_context("Je suis enceinte, puis-je prendre de l'ibuprofène ?")
        assert result.verdict is Verdict.BLOCK

    def test_general_question_on_the_same_topic_passes(self):
        """Same subject, different question. This is why we use `and`, not `or`."""
        result = check_patient_context(
            "Quelles sont les contre-indications de l'ibuprofène chez la femme enceinte ?"
        )
        assert result.verdict is Verdict.PASS

    def test_a_condition_alone_is_not_personal(self):
        result = check_patient_context("Ibuprofène et insuffisance rénale ?")
        assert result.verdict is Verdict.PASS

    def test_a_person_alone_is_not_personal(self):
        result = check_patient_context("Je cherche la posologie du paracétamol.")
        assert result.verdict is Verdict.PASS


class TestBudget:
    def test_under_the_limit_passes(self, monkeypatch):
        monkeypatch.setattr(checks, "get_call_count", lambda: 10)
        assert check_budget().verdict is Verdict.PASS

    def test_near_the_limit_flags(self, monkeypatch):
        monkeypatch.setattr(checks, "get_call_count", lambda: 180)
        assert check_budget().verdict is Verdict.FLAG

    def test_at_the_limit_blocks(self, monkeypatch):
        monkeypatch.setattr(checks, "get_call_count", lambda: 200)
        assert check_budget().verdict is Verdict.BLOCK


class TestRunAll:
    def test_returns_one_result_per_guard(self):
        results = run_all("Quelle est la posologie ?", "500 mg.", [_citation()])
        assert len(results) == 5

    def test_a_bad_answer_shows_every_problem_not_just_the_first(self):
        results = run_all("Quel est le prix ?", "Il coûte 900 DA.", [])
        bloques = [r for r in results if r.verdict is Verdict.BLOCK]
        assert len(bloques) >= 2
