from datetime import date

from conftest import assert_matches
from wealthwise.analysis.subscriptions import find_subscriptions
from wealthwise.contracts import Category, Transaction


def tx(day: date, description: str, amount: float) -> Transaction:
    return Transaction(date=day, description=description, amount=amount, category=Category.SUBSCRIPTIONS)


def test_sample_transactions_give_expected_subscriptions(categorised_profile, expected):
    result = find_subscriptions(categorised_profile.transactions)
    assert_matches([s.model_dump(mode="json") for s in result], expected["subscriptions"])


def test_one_off_and_same_month_charges_are_not_subscriptions():
    result = find_subscriptions([
        tx(date(2026, 7, 1), "DISNEY PLUS", -9.99),
        tx(date(2026, 7, 20), "DISNEY PLUS", -9.99),  # same month twice: still 1 distinct month
        tx(date(2026, 8, 1), "SPOTIFY", -10.99),
    ])
    assert result == []


def test_largest_monthly_amount_first():
    result = find_subscriptions([
        tx(date(2026, 7, 1), "SPOTIFY", -10.0),
        tx(date(2026, 8, 1), "SPOTIFY", -12.0),
        tx(date(2026, 7, 2), "GYM", -40.0),
        tx(date(2026, 8, 2), "GYM", -40.0),
    ])
    assert [(s.name, s.monthly_amount, s.months_seen) for s in result] == [("GYM", 40.0, 2), ("SPOTIFY", 11.0, 2)]
