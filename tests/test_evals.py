import pytest

import wealthwise.rag as rag
from wealthwise import evals

OFFLINE_CASES = [case for case in evals.CASES if not case["needs_model"]]


def test_eval_set_covers_answers_and_guardrails():
    outcomes = {case["outcome"] for case in evals.CASES}

    assert outcomes == {"answer", "declined"}
    assert len(evals.CASES) >= 10


@pytest.mark.parametrize("case", OFFLINE_CASES, ids=[case["question"] for case in OFFLINE_CASES])
def test_offline_cases_pass_both_evaluators(monkeypatch, case):
    monkeypatch.setattr(rag, "get_chat_model", lambda: None)
    profile, report = evals.load_sample()

    outputs = evals.target(profile, report)({"question": case["question"]})
    reference = evals.reference_outputs(case)

    assert evals.outcome_matches(outputs, reference)
    assert evals.figure_present(outputs, reference)


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        (rag._OFF_TOPIC, "declined"),
        (rag._INSUFFICIENT_EVIDENCE, "declined"),
        (rag._NO_OPENROUTER_KEY, "no_key"),
        (rag._APOLOGY, "error"),
        ("Your monthly income averages €3,150.00.", "answer"),
    ],
)
def test_outcome_classifies_guardrail_replies(answer, expected):
    assert evals.outcome(answer) == expected


def test_figure_present_fails_when_the_expected_figure_is_missing():
    assert not evals.figure_present({"answer": "You spent €1.00."}, {"outcome": "answer", "figure": "€287.31"})
    assert evals.figure_present({"answer": "No figure needed."}, {"outcome": "declined", "figure": None})
