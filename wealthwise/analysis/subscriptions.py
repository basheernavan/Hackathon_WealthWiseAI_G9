"""Task B4: find Subscriptions. Spec: docs/specs/02-analysis.md#b4-subscriptions"""

from collections import defaultdict

from wealthwise.contracts import Category, Subscription, Transaction


def find_subscriptions(transactions: list[Transaction]) -> list[Subscription]:
    """`transactions` already have categories set. Largest monthly amount first."""
    groups: dict[str, list[Transaction]] = defaultdict(list)
    for t in transactions:
        if t.category == Category.SUBSCRIPTIONS and t.amount < 0:
            groups[t.description].append(t)

    subscriptions = []
    for name, ts in groups.items():
        months = len({(t.date.year, t.date.month) for t in ts})
        if months >= 2:
            mean_outflow = -sum(t.amount for t in ts) / len(ts)
            subscriptions.append(Subscription(name=name, monthly_amount=round(mean_outflow, 2), months_seen=months))
    return sorted(subscriptions, key=lambda s: s.monthly_amount, reverse=True)
