from conftest import assert_matches
from wealthwise.analysis.plans import build_plans
from wealthwise.contracts import Debt, DebtKind


def test_sample_gives_expected_cuts_debt_plan_and_savings_plan(expected_metrics, sample_profile, expected):
    cuts, debt_plan, savings_plan = build_plans(expected_metrics, sample_profile.debts)
    assert cuts == 107.56
    assert_matches(debt_plan.model_dump(mode="json"), expected["debt_plan"])
    assert_matches(savings_plan.model_dump(mode="json"), expected["savings_plan"])
    available_scenario = round(max(expected_metrics.monthly_surplus, 0) + cuts, 2)
    assert round(debt_plan.extra_monthly_payment + savings_plan.monthly_amount, 2) == available_scenario


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


def test_spending_cuts_first_offset_a_monthly_shortfall_before_allocations(expected_metrics, sample_profile):
    shortfall = expected_metrics.model_copy(update={"monthly_surplus": -100.0})

    cuts, debt_plan, savings_plan = build_plans(shortfall, sample_profile.debts)

    assert cuts == 107.56
    assert debt_plan.extra_monthly_payment == 3.78
    assert savings_plan.monthly_amount == 3.78
    assert round(debt_plan.extra_monthly_payment + savings_plan.monthly_amount, 2) == 7.56


def test_debt_projection_does_not_claim_savings_when_payoff_is_outside_horizon(expected_metrics):
    stuck = Debt(name="Stuck Loan", kind=DebtKind.LOAN, balance=1000, annual_interest_rate=12, monthly_payment=0)
    low_surplus = expected_metrics.model_copy(
        update={"monthly_surplus": 2.0, "spending_by_category": {}}
    )

    _, debt_plan, _ = build_plans(low_surplus, [stuck])

    assert debt_plan.months_to_debt_free_current == 600
    assert debt_plan.months_to_debt_free_with_extra == 600
    assert debt_plan.months_saved == 0
    assert debt_plan.interest_saved == 0.0
