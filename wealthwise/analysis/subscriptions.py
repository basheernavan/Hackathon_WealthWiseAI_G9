"""Task B4: find Subscriptions. Spec: docs/specs/02-analysis.md#b4-subscriptions"""

from wealthwise.contracts import Subscription, Transaction


def find_subscriptions(transactions: list[Transaction]) -> list[Subscription]:
    """`transactions` already have categories set. Largest monthly amount first."""
    raise NotImplementedError("B4 find_subscriptions")
