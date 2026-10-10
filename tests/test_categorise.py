from datetime import date

from wealthwise.analysis.categorise import categorise
from wealthwise.contracts import Category, Transaction


def tx(description: str, amount: float = -10.0) -> Transaction:
    return Transaction(date=date(2026, 7, 1), description=description, amount=amount)


def test_sample_transactions_get_the_answer_key_categories(sample_profile, expected):
    result = categorise(sample_profile.transactions)
    assert [t.category.value for t in result] == expected["transaction_categories"]


def test_uber_eats_is_takeaway_and_uber_is_transport():
    assert [t.category for t in categorise([tx("UBER EATS DUBLIN"), tx("UBER *TRIP")])] == [
        Category.TAKEAWAY,
        Category.TRANSPORT,
    ]


def test_positive_amount_is_income_and_unknown_is_other():
    assert [t.category for t in categorise([tx("TESCO REFUND", 5.0), tx("RANDOM SHOP")])] == [
        Category.INCOME,
        Category.OTHER,
    ]


def test_keyword_matches_whole_words_only():
    assert categorise([tx("PARENTAL GIFT")])[0].category == Category.OTHER  # contains "RENT" inside a word


def test_input_is_not_mutated(sample_profile):
    categorise(sample_profile.transactions)
    assert all(t.category is None for t in sample_profile.transactions)
