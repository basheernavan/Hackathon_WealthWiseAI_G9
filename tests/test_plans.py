from conftest import assert_matches
from wealthwise.analysis.plans import build_plans
from wealthwise.contracts import Debt, DebtKind


def test_sample_gives_expected_cuts_debt_plan_and_savings_plan(expected_metrics, sample_profile, expected):
    cuts, debt_plan, savings_plan = build_plans(expected_metrics, sample_profile.debts)
    assert cuts == 107.56
    assert_matches(debt_plan.model_dump(mode="json"), expected["debt_plan"])
    assert_matches(savings_plan.model_dump(mode="json"), expected["savings_plan"])


def test_no_debts_gives_no_debt_plan_and_savings_gets_all_freed_money(expected_metrics):
    cuts, debt_plan, savings_plan = build_plans(expected_metrics, [])
    assert debt_plan is None
    assert savings_plan.monthly_amount == round(214.4 + 107.56, 2)


def test_debt_that_never_shrinks_stops_at_600_months(expected_metrics):
    stuck = Debt(name="Stuck Loan", kind=DebtKind.LOAN, balance=1000, annual_interest_rate=12, monthly_payment=0)
    zero = expected_metrics.model_copy(update={"monthly_surplus": 0.0, "spending_by_category": {}})
    _, debt_plan, savings_plan = build_plans(zero, [stuck])
    assert debt_plan.months_to_debt_free_current == 600
    assert savings_plan.months_to_target is None
