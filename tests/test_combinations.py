"""Combination tests: every test_data/ folder against report invariants, plus score, categoriser, parser and plan tables.

Known defects (docs/test-report.md section 5) are written as strict xfail tests: they report XFAIL today and
turn into a failure (XPASS) the moment someone fixes the defect, as a reminder to remove the marker.
"""

from pathlib import Path

import pytest

from wealthwise.analysis import build_report
from wealthwise.analysis.categorise import categorise, category_for
from wealthwise.analysis.metrics import compute_metrics
from wealthwise.analysis.plans import avalanche_order, build_plans, simulate
from wealthwise.analysis.score import score_health
from wealthwise.contracts import (
    Category,
    Debt,
    DebtKind,
    FinancialProfile,
    Metrics,
    Report,
    Transaction,
    UploadedDocument,
)
from wealthwise.ingestion import load_profile
from wealthwise.ingestion.bank_csv import parse_bank_csv
from wealthwise.ingestion.detect import detect_document_type
from wealthwise.ingestion.loan_pdf import title

TEST_DATA = Path(__file__).resolve().parents[1] / "test_data"
FOLDERS = sorted(p.name for p in TEST_DATA.iterdir() if p.is_dir())
_cache: dict[str, tuple[FinancialProfile, Report]] = {}


def run(folder: str) -> tuple[FinancialProfile, Report]:
    if folder not in _cache:
        docs = [UploadedDocument(filename=f.name, content=f.read_bytes()) for f in sorted((TEST_DATA / folder).iterdir())]
        profile = load_profile(docs)
        _cache[folder] = (profile, build_report(profile))
    return _cache[folder]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


# ---------- A. Report invariants, every folder (12 folders x 12 checks) ----------


@pytest.mark.parametrize("folder", FOLDERS)
def test_score_is_0_to_100_and_band_matches(folder):
    s = run(folder)[1].health_score
    assert 0 <= s.score <= 100
    assert s.band == ("good" if s.score >= 75 else "fair" if s.score >= 50 else "needs attention")


@pytest.mark.parametrize("folder", FOLDERS)
def test_four_components_with_max_points_100(folder):
    comps = run(folder)[1].health_score.components
    assert [c.name for c in comps] == ["savings_rate", "debt_to_income", "emergency_fund", "discretionary_share"]
    assert sum(c.max_points for c in comps) == 100
    assert all(0 <= c.points <= c.max_points for c in comps)


@pytest.mark.parametrize("folder", FOLDERS)
def test_score_is_the_rounded_sum_of_component_points(folder):
    s = run(folder)[1].health_score
    assert abs(s.score - sum(c.points for c in s.components)) <= 0.51


@pytest.mark.parametrize("folder", FOLDERS)
def test_surplus_is_income_minus_spending(folder):
    m = run(folder)[1].metrics
    assert m.monthly_surplus == pytest.approx(m.monthly_income - m.monthly_spending, abs=0.011)


@pytest.mark.parametrize("folder", FOLDERS)
def test_category_spending_adds_up_to_total_spending(folder):
    m = run(folder)[1].metrics
    assert sum(m.spending_by_category.values()) == pytest.approx(m.monthly_spending, abs=0.1)
    assert all(v >= 0 for v in m.spending_by_category.values())


@pytest.mark.parametrize("folder", FOLDERS)
def test_every_transaction_gets_a_category(folder):
    profile, _ = run(folder)
    assert all(t.category is not None for t in categorise(profile.transactions))


@pytest.mark.parametrize("folder", FOLDERS)
def test_report_survives_a_json_round_trip(folder):
    report = run(folder)[1]
    assert Report.model_validate_json(report.model_dump_json()) == report


@pytest.mark.parametrize("folder", FOLDERS)
def test_three_agents_each_give_one_recommendation(folder):
    assert [r.agent for r in run(folder)[1].recommendations] == ["spending", "debt", "savings"]


@pytest.mark.parametrize("folder", FOLDERS)
def test_savings_target_is_three_months_of_spending(folder):
    r = run(folder)[1]
    assert r.savings_plan.target_amount == pytest.approx(3 * r.metrics.monthly_spending, abs=0.011)


@pytest.mark.parametrize("folder", FOLDERS)
def test_months_to_target_is_none_only_without_savings(folder):
    plan = run(folder)[1].savings_plan
    assert (plan.months_to_target is None) == (plan.monthly_amount <= 0)


@pytest.mark.parametrize("folder", FOLDERS)
def test_debt_plan_exists_exactly_when_debts_exist(folder):
    profile, report = run(folder)
    assert (report.debt_plan is not None) == bool(profile.debts)
    if report.debt_plan:
        assert report.debt_plan.months_to_debt_free_with_extra <= report.debt_plan.months_to_debt_free_current
        assert report.debt_plan.payoff_order[0] == avalanche_order(profile.debts)[0].name


@pytest.mark.parametrize("folder", FOLDERS)
def test_offline_run_uses_template_text(folder):
    assert run(folder)[1].llm_used is False


# ---------- B. Score table: hand-worked cases (savings, debt-to-income, cushion months, discretionary) -> score, band ----------

SCORES = [
    ((0.0, 0.50, 0.0, 0.50), 0, "needs attention"),
    ((0.20, 0.10, 3.0, 0.20), 100, "good"),
    ((0.10, 0.30, 1.5, 0.35), 50, "fair"),
    ((0.20, 0.50, 0.0, 0.50), 30, "needs attention"),
    ((0.0, 0.10, 3.0, 0.20), 70, "fair"),
    ((0.20, 0.10, 0.0, 0.20), 80, "good"),
    ((0.20, 0.10, 3.0, 0.50), 80, "good"),
    ((0.20, 0.10, 3.0, 0.80), 80, "good"),
    ((-0.50, 0.10, 3.0, 0.20), 70, "fair"),
    ((0.05, 0.10, 3.0, 0.20), 78, "good"),
    ((0.20, 0.10, 2.25, 0.50), 75, "good"),
    ((0.20, 0.10, 2.10, 0.50), 74, "fair"),
    ((0.20, 0.50, 3.0, 0.50), 50, "fair"),
    ((0.20, 0.50, 2.90, 0.50), 49, "needs attention"),
    ((0.005, 0.50, 0.0, 0.50), 1, "needs attention"),
    ((0.0, 0.90, 0.0, 0.50), 0, "needs attention"),
    ((0.20, 0.30, 3.0, 0.50), 65, "fair"),
    ((0.20, 0.10, 6.0, 0.20), 100, "good"),
    ((0.20, 0.10, 3.0, 0.0), 100, "good"),
    ((1.0, 0.0, 12.0, 0.0), 100, "good"),
]


def metrics_with(savings, dti, cushion, disc) -> Metrics:
    return Metrics(months_covered=1, monthly_income=3000, monthly_spending=2000, monthly_surplus=1000, spending_by_category={},
                   savings_rate=savings, debt_to_income=dti, total_debt=0, current_balance=0, emergency_fund_months=cushion,
                   discretionary_share=disc)


@pytest.mark.parametrize("inputs, score, band", SCORES, ids=[f"score{i + 1}" for i in range(len(SCORES))])
def test_score_for_hand_worked_metrics(inputs, score, band):
    result = score_health(metrics_with(*inputs))
    assert (result.score, result.band) == (score, band)


# ---------- C. Categoriser: description x sign -> category ----------

CATEGORIES = [
    ("Tesco Grocery", Category.GROCERIES), ("LIDL", Category.GROCERIES), ("Aldi", Category.GROCERIES), ("Dunnes Stores", Category.GROCERIES),
    ("Supervalu", Category.GROCERIES), ("tesco", Category.GROCERIES), ("Deliveroo", Category.TAKEAWAY), ("Just Eat", Category.TAKEAWAY),
    ("Uber Eats", Category.TAKEAWAY), ("Restaurant", Category.TAKEAWAY), ("Starbucks", Category.TAKEAWAY), ("Uber", Category.TRANSPORT),
    ("Leap Card", Category.TRANSPORT), ("Circle K", Category.TRANSPORT), ("Irish Rail", Category.TRANSPORT), ("Petrol", Category.TRANSPORT),
    ("Electric Ireland", Category.UTILITIES), ("Bord Gais", Category.UTILITIES), ("Utility Bill", Category.UTILITIES),
    ("Vodafone", Category.UTILITIES), ("Netflix Subscription", Category.SUBSCRIPTIONS), ("Spotify", Category.SUBSCRIPTIONS),
    ("Disney Subscription", Category.SUBSCRIPTIONS), ("Flyefit Gym", Category.SUBSCRIPTIONS), ("Gym Membership", Category.SUBSCRIPTIONS),
    ("Amazon", Category.SHOPPING), ("Zara", Category.SHOPPING), ("Penneys", Category.SHOPPING), ("IKEA", Category.SHOPPING),
    ("Cinema", Category.ENTERTAINMENT), ("Pub", Category.ENTERTAINMENT), ("Ticketmaster", Category.ENTERTAINMENT),
    ("Brazen Head", Category.ENTERTAINMENT), ("Rent Payment", Category.HOUSING), ("Mortgage", Category.HOUSING),
    ("Loan Repayment", Category.DEBT_REPAYMENT), ("Credit Card Payment", Category.DEBT_REPAYMENT),
    ("ACME Dental", Category.OTHER), ("Joe's Hardware", Category.OTHER), ("Mystery Transfer", Category.OTHER),
    ("Eirmax Ltd", Category.OTHER), ("Rental Car", Category.OTHER), ("", Category.OTHER),
]


def tx(description: str, amount: float, day: int = 1, balance: float | None = None) -> Transaction:
    return Transaction(date=f"2026-03-{day:02d}", description=description, amount=amount, balance=balance)


@pytest.mark.parametrize("description, expected", CATEGORIES)
def test_money_out_is_categorised_by_description(description, expected):
    assert category_for(tx(description, -10)) == expected


@pytest.mark.parametrize("description", ["Tesco refund", "Monthly Salary Credit", "Netflix reversal", "Rent received", "Unknown"])
def test_any_money_in_is_income(description):
    assert category_for(tx(description, 25)) == Category.INCOME


# ---------- D. Parsers and loader ----------

CSV_OK = b"Date,Description,Amount,Balance\n2026-03-01,Tesco,-50.00,950.00\n2026-03-02,Salary,2000.00,2950.00\n"


def test_signed_csv_keeps_signs_and_balances():
    transactions, warnings = parse_bank_csv(CSV_OK)
    assert [t.amount for t in transactions] == [-50.0, 2000.0]
    assert [t.balance for t in transactions] == [950.0, 2950.0]
    assert warnings == []


def test_csv_with_a_byte_order_mark_still_parses():
    assert len(parse_bank_csv(b"\xef\xbb\xbf" + CSV_OK)[0]) == 2


@pytest.mark.parametrize("bad_row", ["not-a-date,Tesco,-5,10", "2026-03-01,Tesco,abc,10", "2026-03-01,Tesco,-5,xyz", "2026-13-40,Tesco,-5,10"])
def test_csv_skips_unreadable_rows_with_a_warning(bad_row):
    transactions, warnings = parse_bank_csv(b"Date,Description,Amount,Balance\n" + bad_row.encode() + b"\n2026-03-02,Salary,5,5\n")
    assert len(transactions) == 1
    assert any("Skipped row 1" in w for w in warnings)


def test_unsigned_csv_treats_salary_and_refund_as_income_and_the_rest_as_spending():
    transactions, warnings = parse_bank_csv(b"Date,Category,Amount\n2026-03-01,Salary,100\n2026-03-02,Refund,5\n2026-03-03,Rent,40\n")
    assert [t.amount for t in transactions] == [100.0, 5.0, -40.0]
    assert any("no sign" in w for w in warnings)


def test_empty_csv_gives_no_transactions():
    assert parse_bank_csv(b"Date,Description,Amount,Balance\n")[0] == []


@pytest.mark.parametrize("filename, content", [("notes.txt", b"hello"), ("empty.pdf", b""), ("broken.pdf", b"%PDF-garbage"), ("photo.png", b"\x89PNG")])
def test_unsupported_or_unreadable_files_have_no_type(filename, content):
    assert detect_document_type(filename, content) is None


@pytest.mark.parametrize("folder", [f for f in FOLDERS if f != "wrong_closing_balance_nov_2026"])
def test_files_in_every_folder_are_recognised(folder):
    for f in (TEST_DATA / folder).iterdir():
        assert detect_document_type(f.name, f.read_bytes()) is not None, f.name


def test_only_unsupported_files_raise():
    with pytest.raises(ValueError, match="No supported documents"):
        load_profile([UploadedDocument(filename="notes.txt", content=b"hello")])


def test_unsupported_file_next_to_a_good_one_only_warns():
    good = (TEST_DATA / "best_saver_mar_2026" / "Bank_Statement_March_2026.pdf").read_bytes()
    profile = load_profile([UploadedDocument(filename="notes.txt", content=b"hello"), UploadedDocument(filename="b.pdf", content=good)])
    assert any("Could not recognise" in w for w in profile.sources[0].warnings)
    assert len(profile.transactions) == 8


def test_transactions_from_two_months_are_merged_in_date_order():
    march = (TEST_DATA / "best_saver_mar_2026" / "Bank_Statement_March_2026.pdf").read_bytes()
    april = (TEST_DATA / "good_small_loan_apr_2026" / "Bank_Statement_April_2026.pdf").read_bytes()
    profile = load_profile([UploadedDocument(filename="apr.pdf", content=april), UploadedDocument(filename="mar.pdf", content=march)])
    dates = [t.date for t in profile.transactions]
    assert dates == sorted(dates) and len(dates) == 19
    assert compute_metrics(profile.model_copy(update={"transactions": categorise(profile.transactions)})).months_covered == 2


def test_the_same_statement_uploaded_twice_is_counted_once():
    pdf = (TEST_DATA / "best_saver_mar_2026" / "Bank_Statement_March_2026.pdf").read_bytes()
    profile = load_profile([UploadedDocument(filename="a.pdf", content=pdf), UploadedDocument(filename="b.pdf", content=pdf)])
    assert len(profile.transactions) == 8
    assert any("Overlaps a.pdf" in w for w in profile.sources[1].warnings)


# ---------- E. Plans and metrics edge cases ----------


def debt(name="Loan", balance=1200.0, apr=0.0, payment=100.0) -> Debt:
    return Debt(name=name, kind=DebtKind.LOAN, balance=balance, annual_interest_rate=apr, monthly_payment=payment)


def test_interest_free_debt_clears_in_balance_over_payment_months():
    assert simulate([debt()], 0.0) == (12, 0.0)


@pytest.mark.parametrize("extra, months", [(0, 12), (100, 6), (300, 3), (1200, 1)])
def test_extra_payment_shortens_an_interest_free_debt(extra, months):
    assert simulate([debt()], extra)[0] == months


def test_interest_makes_the_debt_last_longer_and_cost_more():
    free, taxed = simulate([debt()], 0.0), simulate([debt(apr=20.0)], 0.0)
    assert taxed[0] > free[0] and taxed[1] > 0


def test_avalanche_orders_by_rate_then_smaller_balance():
    debts = [debt("low", 500, 5.0), debt("high big", 900, 20.0), debt("high small", 100, 20.0)]
    assert [d.name for d in avalanche_order(debts)] == ["high small", "high big", "low"]


def test_empty_profile_gives_all_zero_metrics():
    m = compute_metrics(FinancialProfile())
    assert (m.months_covered, m.monthly_income, m.monthly_spending, m.savings_rate, m.emergency_fund_months) == (0, 0.0, 0.0, 0.0, 0.0)


def test_income_only_profile_has_full_savings_rate():
    profile = FinancialProfile(transactions=categorise([tx("Salary", 1000, balance=1000.0)]))
    assert compute_metrics(profile).savings_rate == 1.0


def test_zero_surplus_gives_zero_extra_payment_and_no_target_date():
    m = metrics_with(0.0, 0.1, 0.0, 0.1).model_copy(update={"monthly_surplus": 0.0, "spending_by_category": {}})
    cuts, plan, savings = build_plans(m, [debt()])
    assert (cuts, plan.extra_monthly_payment, savings.monthly_amount, savings.months_to_target) == (0.0, 0.0, 0.0, None)


def test_takeaway_cut_is_half_of_takeaway_spending():
    m = metrics_with(0.2, 0.0, 3.0, 0.2).model_copy(update={"spending_by_category": {Category.TAKEAWAY: 201.0}})
    assert build_plans(m, [])[0] == 100.5


# ---------- F. Known defects (strict xfail: they flip to a failure when fixed) ----------


@pytest.mark.xfail(strict=True, reason="BUG-1: loan_pdf.title() keeps 'OF' upper case")
def test_lender_name_casing_in_loan_pdf():
    assert title("BANK OF IRELAND PERSONAL LOAN") == "Bank of Ireland Personal Loan"


@pytest.mark.xfail(strict=True, reason="WEAK-2: debt card shows 'Adding EUR 0.00/month' when there is no surplus")
def test_debt_advice_does_not_promise_nothing():
    debt_card = next(r for r in run("worst_overspender_jun_2026")[1].recommendations if r.agent == "debt")
    assert "EUR 0.00/month" not in debt_card.detail


@pytest.mark.xfail(strict=True, reason="WEAK-3: only takeaways are ever flagged for cutting")
def test_worst_case_advice_mentions_more_than_takeaways():
    spending_cards = [r for r in run("worst_overspender_jun_2026")[1].recommendations if r.agent == "spending"]
    assert any("shopping" in r.detail.lower() or "entertainment" in r.detail.lower() for r in spending_cards)


@pytest.mark.xfail(strict=True, reason="WEAK-4: best saver is told to 'Build a 3-month emergency fund'")
def test_best_saver_is_not_told_to_build_an_emergency_fund():
    savings_card = next(r for r in run("best_saver_mar_2026")[1].recommendations if r.agent == "savings")
    assert "Build a 3-month emergency fund" not in savings_card.title


@pytest.mark.xfail(strict=True, reason="WEAK-6: a CSV without a balance column gives no warning about the cushion score")
def test_csv_without_balance_warns_about_the_emergency_fund():
    profile, _ = run("messy_csv_only_nov_2026")
    assert any("balance" in w.lower() for s in profile.sources for w in s.warnings)


@pytest.mark.xfail(strict=True, reason="WEAK-7: uncategorised spending is not reported to the user")
def test_large_uncategorised_spending_is_reported():
    profile, report = run("messy_csv_only_nov_2026")
    assert report.metrics.spending_by_category[Category.OTHER] > 0.2 * report.metrics.monthly_spending
    assert any("categor" in w.lower() for s in profile.sources for w in s.warnings)
