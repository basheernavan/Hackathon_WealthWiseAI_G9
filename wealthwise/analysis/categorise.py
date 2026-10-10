"""Task B1: keyword categoriser. Spec: docs/specs/02-analysis.md#b1-categorise"""

from wealthwise.contracts import Transaction


def categorise(transactions: list[Transaction]) -> list[Transaction]:
    """Return copies of the transactions, same order, each with `category` set."""
    raise NotImplementedError("B1 categorise")
