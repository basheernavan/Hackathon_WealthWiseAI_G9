"""Task B1: keyword categoriser. Spec: docs/specs/02-analysis.md#b1-categorise"""

import re

from wealthwise.contracts import Category, Transaction

# First match wins, so order matters: "UBER EATS" (takeaway) is checked before "UBER" (transport).
RULES: list[tuple[Category, list[str]]] = [
    (Category.DEBT_REPAYMENT, ["LOAN REPAYMENT", "CREDIT CARD PAYMENT"]),
    (Category.HOUSING, ["RENT", "MORTGAGE"]),
    (Category.GROCERIES, ["TESCO", "LIDL", "ALDI", "SUPERVALU", "DUNNES"]),
    (Category.TAKEAWAY, ["DELIVEROO", "JUST EAT", "UBER EATS"]),
    (Category.TRANSPORT, ["LEAP CARD", "CIRCLE K", "IRISH RAIL", "UBER"]),
    (Category.UTILITIES, ["ELECTRIC IRELAND", "BORD GAIS", "EIR", "THREE MOBILE", "VODAFONE"]),
    (Category.SUBSCRIPTIONS, ["NETFLIX", "SPOTIFY", "DISNEY", "FLYEFIT", "GYM"]),
    (Category.SHOPPING, ["AMAZON", "ZARA", "PENNEYS", "IKEA"]),
    (Category.ENTERTAINMENT, ["CINEWORLD", "TICKETMASTER", "PUB", "BRAZEN HEAD"]),
]
PATTERNS = [
    (category, re.compile(r"\b(?:" + "|".join(map(re.escape, keywords)) + r")\b", re.IGNORECASE))
    for category, keywords in RULES
]


def category_for(transaction: Transaction) -> Category:
    if transaction.amount > 0:
        return Category.INCOME
    return next((c for c, p in PATTERNS if p.search(transaction.description)), Category.OTHER)


def categorise(transactions: list[Transaction]) -> list[Transaction]:
    """Return copies of the transactions, same order, each with `category` set."""
    return [t.model_copy(update={"category": category_for(t)}) for t in transactions]
