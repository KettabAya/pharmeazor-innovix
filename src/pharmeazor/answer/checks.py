"""Les gardes. Each one checks the answer before we show it.

Five problems: wrong number, no source, question not ours, personal advice,
too many API calls. None of them calls the model.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum

from ..schemas import Citation
from .llm_client import get_call_count
from .number_guard import verify

__all__ = [
    "Verdict",
    "CheckResult",
    "MAX_LLM_CALLS",
    "check_numbers",
    "check_sources_present",
    "check_out_of_scope",
    "check_patient_context",
    "check_budget",
    "run_all",
]


class Verdict(Enum):
    PASS = "pass"
    FLAG = "flag"
    BLOCK = "block"


@dataclass(frozen=True)
class CheckResult:
    verdict: Verdict
    reason: str


def _aplatir(texte: str) -> str:
    """Lowercase, no accents. People write ENCEINTE, enceinte, enceınte."""
    decompose = unicodedata.normalize("NFKD", (texte or "").lower())
    return "".join(c for c in decompose if not unicodedata.combining(c))


def check_numbers(answer: str, citations: list[Citation]) -> CheckResult:
    """Every number must be in one of the cited passages."""
    passages = [c.passage.text for c in citations]
    rapport = verify(answer, passages)
    if rapport.passed:
        return CheckResult(Verdict.PASS, rapport.summary_fr())
    return CheckResult(Verdict.BLOCK, rapport.summary_fr())


def check_sources_present(
    answer: str,
    citations: list[Citation],
    est_un_refus: bool = False,
) -> CheckResult:
    """No source, no medical answer.

    The caller tells us if it is a refusal. I don't guess it from the text,
    because the model changes its words.
    """
    if est_un_refus:
        return CheckResult(Verdict.PASS, "Refus : aucune source à citer.")

    if not citations:
        return CheckResult(
            Verdict.BLOCK,
            "Aucune source citée. Une information médicale ne s'affiche pas "
            "sans le passage qui la porte.",
        )

    return CheckResult(Verdict.PASS, f"Sources citées : {len(citations)} passage(s).")


# We have 5 sections only. Price is not one of them.
# Checked 26/11/2026: PPA is empty on all 1 650 products.
# But BM25 still gives 8.98 to a price question, because the drug name is
# in the corpus. So search does not stop it. We stop it here.
HORS_PERIMETRE: dict[str, tuple[str, ...]] = {
    "le prix": (
        "prix",
        "tarif",
        "cout",
        "coute",
        "combien coute",
        "remboursement",
        "rembourse",
        "price",
        "retail",
        "cost",
        "how much",
        "pay",
    ),
    "la disponibilité en pharmacie": (
        "en stock",
        "disponible en pharmacie",
        "ou acheter",
        "ou trouver",
        "rupture de stock",
        "available",
        "in stock",
        "near me",
        "pharmacy near",
    ),
    "les conditions de délivrance": (
        "ordonnance obligatoire",
        "sans ordonnance",
        "prescription required",
        "over the counter",
        "je dois prendre",
        "dois-je prendre",
        "quel médicament prendre",
        "que prendre",
        "conseillez-moi",
        "conseil personnalisé",
        "which should i take",
        "which one should i take",
        "which antibiotic should a patient",
        "which antihypertensive",
        "best for a specific patient",
        "best for a particular patient",
        "which is best for",
        "what should a patient take",
        "which antibiotic should a particular patient",
        "which antibiotic should a specific patient",
    ),
}


def check_out_of_scope(question: str) -> CheckResult:
    """Is the question inside our 5 sections?

    The list is short and it misses some ways of asking. That is ok: I can
    add a word later. Blocking a good question is worse.
    """
    plat = _aplatir(question)
    for sujet, marqueurs in HORS_PERIMETRE.items():
        for marqueur in marqueurs:
            if marqueur in plat:
                return CheckResult(
                    Verdict.BLOCK,
                    f"Question sur {sujet} : cette information n'est pas dans "
                    "nos sources. Nous couvrons les indications, la posologie, "
                    "les contre-indications, les interactions et les effets "
                    "indésirables.",
                )
    return CheckResult(Verdict.PASS, "Question dans le périmètre.")


# Two lists. We need one word from each: a person AND a condition.
#
#   "contre-indications chez la femme enceinte ?"   -> condition only, pass
#   "je suis enceinte, puis-je en prendre ?"        -> both, block
#
# First try I used `or` and it blocked every question with "enceinte".
_PERSONNES = re.compile(
    r"(\bje\b|j ai\b|\bma \b|\bmon \b|\bmes \b|\bmoi\b|puis-je|dois-je|"
    r"\brani\b|\brania\b|\bmon fils\b|\bma fille\b|\bma femme\b|"
    r"\bmon patient\b|\bma patiente\b)"
)
_ETATS = re.compile(
    r"\b(enceinte|grossesse|allaite|allaitement|insuffisance renale|"
    r"insuffisant renal|insuffisance hepatique|diabetique|diabete|"
    r"asthmatique|asthme|epileptique|hypertendu|anticoagulant|hamla)\b"
)


def check_patient_context(question: str) -> CheckResult:
    """A question about one patient is not a question about a drug.

    We know the general contre-indication. We don't know the month, the other
    drugs, or what the doctor said. So it is the pharmacist who decides.
    """
    plat = _aplatir(question)
    personne = _PERSONNES.search(plat)
    etat = _ETATS.search(plat)

    if personne and etat:
        return CheckResult(
            Verdict.BLOCK,
            "Cette question porte sur une situation personnelle. Les "
            "contre-indications générales du médicament sont consultables, "
            "mais la décision revient au pharmacien, qui connaît le dossier.",
        )

    return CheckResult(Verdict.PASS, "Question d'ordre général.")


# Free Groq key, and .env.example says never add a payment method.
# A loop calling the model would burn the key for the whole team.
# This number should go to config.py, but that is a team decision.
MAX_LLM_CALLS = 200
SEUIL_ALERTE = 0.8


def check_budget() -> CheckResult:
    """How many model calls did we use already?"""
    appels = get_call_count()

    if appels >= MAX_LLM_CALLS:
        return CheckResult(
            Verdict.BLOCK,
            f"Budget d'appels épuisé : {appels}/{MAX_LLM_CALLS}. "
            "Le quota gratuit protège la clé de toute l'équipe.",
        )

    if appels >= MAX_LLM_CALLS * SEUIL_ALERTE:
        return CheckResult(
            Verdict.FLAG,
            f"Budget d'appels presque atteint : {appels}/{MAX_LLM_CALLS}.",
        )

    return CheckResult(Verdict.PASS, f"Appels au modèle : {appels}/{MAX_LLM_CALLS}.")


def run_all(
    question: str,
    answer: str,
    citations: list[Citation],
    est_un_refus: bool = False,
) -> list[CheckResult]:
    """Run the five guards and give back the five results.

    The two that read only the question go first. A question we don't answer
    should not cost us an answer.

    I don't stop at the first BLOCK. If a question has three problems, the
    person should see three.
    """
    return [
        check_patient_context(question),
        check_out_of_scope(question),
        check_budget(),
        check_sources_present(answer, citations, est_un_refus),
        check_numbers(answer, citations),
    ]
