"""Generate the fictional sample documents and answer keys in samples/.

Run: python scripts/generate_samples.py
Deterministic (seeded), so re-running produces identical files.
The answer key is computed here independently of wealthwise.analysis, using the
formulas in docs/specs/02-analysis.md, so analysis tests have a separate oracle.
"""

import csv
import json
import math
import random
import re
import sys
from datetime import date
from pathlib import Path

import openpyxl
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wealthwise.contracts import (  # noqa: E402
    DISCRETIONARY_CATEGORIES,
    Category,
    FinancialProfile,
    Report,
)

OUT = ROOT / "samples"
SAMPLE_NOTE = "SAMPLE - fictional data for WealthWise testing"
PERSON = "Alex Murphy"
BANK = "Northwind Bank"
EMPLOYER = "Acme Analytics Ltd"
OPENING_BALANCE = 3200.00
MONTHS = [(2026, 7), (2026, 8), (2026, 9)]
NET_PAY = 3150.00
PAYSLIP = {
    "gross_pay": 4200.00,
    "deductions": {"Income Tax (PAYE)": 640.00, "PRSI": 168.00, "USC": 142.00, "Pension Contribution": 100.00},
}
DEBTS = [
    {"lender": BANK, "product": "Car Loan", "type": "Loan", "kind": "loan",
     "balance": 7800.00, "apr": 8.9, "payment": 285.00},
    {"lender": BANK, "product": "Visa Credit Card", "type": "Credit Card", "kind": "credit_card",
     "balance": 2100.00, "apr": 21.9, "payment": 120.00},
]

FIXED = [  # (day, description, amount, category)
    (1, "RENT - HARBOUR PROPERTY MGMT", -1350.00, Category.HOUSING),
    (2, "NETFLIX.COM", -15.99, Category.SUBSCRIPTIONS),
    (3, "ELECTRIC IRELAND DD", -85.00, Category.UTILITIES),
    (5, "LOAN REPAYMENT NORTHWIND BANK", -285.00, Category.DEBT_REPAYMENT),
    (7, "SPOTIFY", -11.99, Category.SUBSCRIPTIONS),
    (10, "EIR BROADBAND", -55.00, Category.UTILITIES),
    (12, "FLYEFIT GYM", -39.99, Category.SUBSCRIPTIONS),
    (15, "THREE MOBILE", -30.00, Category.UTILITIES),
    (20, "CREDIT CARD PAYMENT NORTHWIND VISA", -120.00, Category.DEBT_REPAYMENT),
    (25, "SALARY ACME ANALYTICS LTD", NET_PAY, Category.INCOME),
]
VARIABLE = [  # (count, merchants, min, max, category)
    (5, ["TESCO", "LIDL", "ALDI"], 55, 95, Category.GROCERIES),
    (6, ["DELIVEROO", "JUST EAT", "UBER EATS"], 22, 48, Category.TAKEAWAY),
    (3, ["AMAZON.IE", "ZARA", "PENNEYS"], 30, 90, Category.SHOPPING),
    (2, ["CINEWORLD", "TICKETMASTER", "THE BRAZEN HEAD PUB"], 20, 60, Category.ENTERTAINMENT),
]

# Keyword rules from docs/specs/02-analysis.md, used here only to self-check the data.
RULES = [
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


def categorise(description: str, amount: float) -> Category:
    if amount > 0:
        return Category.INCOME
    for category, keywords in RULES:
        if any(re.search(rf"\b{re.escape(k)}\b", description, re.IGNORECASE) for k in keywords):
            return category
    return Category.OTHER


def build_transactions() -> list[dict]:
    rng = random.Random(42)
    rows = []
    for year, month in MONTHS:
        month_rows = [(d, desc, amt, cat) for d, desc, amt, cat in FIXED]
        month_rows += [(day, "LEAP CARD TOP-UP", -40.00, Category.TRANSPORT) for day in (4, 14, 24)]
        for count, merchants, lo, hi, cat in VARIABLE:
            for _ in range(count):
                month_rows.append((rng.randint(1, 28), rng.choice(merchants), -round(rng.uniform(lo, hi), 2), cat))
        month_rows.sort(key=lambda r: r[0])
        for day, desc, amt, cat in month_rows:
            rows.append({"date": date(year, month, day), "description": desc, "amount": amt, "category": cat})
    balance = OPENING_BALANCE
    for r in rows:
        balance = round(balance + r["amount"], 2)
        assert balance >= 0, f"balance went negative on {r['date']}"
        r["balance"] = balance
        assert categorise(r["description"], r["amount"]) == r["category"], r
    return rows


# ---------- Answer-key formulas (mirror docs/specs/02-analysis.md) ----------


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def simulate(debts: list[dict], extra: float) -> tuple[int, float]:
    bal = {d["product"]: d["balance"] for d in debts}
    order = [d["product"] for d in sorted(debts, key=lambda d: (-d["apr"], d["balance"]))]
    budget = sum(d["payment"] for d in debts) + extra
    months, interest = 0, 0.0
    while any(b > 0.005 for b in bal.values()):
        months += 1
        assert months <= 600
        for d in debts:
            i = bal[d["product"]] * d["apr"] / 100 / 12
            bal[d["product"]] += i
            interest += i
        remaining = budget
        for d in debts:
            pay = min(d["payment"], bal[d["product"]])
            bal[d["product"]] -= pay
            remaining -= pay
        for name in order:
            pay = min(remaining, bal[name])
            bal[name] -= pay
            remaining -= pay
    return months, interest


def answer_key(txs: list[dict]) -> dict:
    months = len({(t["date"].year, t["date"].month) for t in txs})
    income = sum(t["amount"] for t in txs if t["category"] == Category.INCOME) / months
    spending = -sum(t["amount"] for t in txs if t["amount"] < 0) / months
    by_cat: dict[Category, float] = {}
    for t in txs:
        if t["amount"] < 0:
            by_cat[t["category"]] = by_cat.get(t["category"], 0.0) - t["amount"] / months
    surplus = income - spending
    debt_payments = sum(d["payment"] for d in DEBTS)
    total_debt = sum(d["balance"] for d in DEBTS)
    current_balance = txs[-1]["balance"]
    emergency = current_balance / spending
    discretionary = sum(v for c, v in by_cat.items() if c in DISCRETIONARY_CATEGORIES) / spending
    savings_rate = surplus / income
    dti = debt_payments / income

    components = [
        ("savings_rate", savings_rate, 30 * clamp01(savings_rate / 0.20), 30),
        ("debt_to_income", dti, 30 * clamp01((0.50 - dti) / 0.40), 30),
        ("emergency_fund", emergency, 20 * clamp01(emergency / 3), 20),
        ("discretionary_share", discretionary, 20 * clamp01((0.50 - discretionary) / 0.30), 20),
    ]
    score = math.floor(sum(c[2] for c in components) + 0.5)
    band = "good" if score >= 75 else "fair" if score >= 50 else "needs attention"

    subs: dict[str, list[dict]] = {}
    for t in txs:
        if t["category"] == Category.SUBSCRIPTIONS:
            subs.setdefault(t["description"], []).append(t)
    subscriptions = sorted(
        (
            {"name": name, "monthly_amount": round(-sum(t["amount"] for t in ts) / len(ts), 2),
             "months_seen": len({(t["date"].year, t["date"].month) for t in ts})}
            for name, ts in subs.items()
            if len({(t["date"].year, t["date"].month) for t in ts}) >= 2
        ),
        key=lambda s: -s["monthly_amount"],
    )

    identified_cuts = round(0.5 * by_cat.get(Category.TAKEAWAY, 0.0), 2)
    freed = max(surplus, 0.0) + identified_cuts
    extra = round(freed / 2, 2)
    savings_monthly = round(freed - extra, 2)
    m_cur, i_cur = simulate(DEBTS, 0.0)
    m_new, i_new = simulate(DEBTS, extra)
    target = round(3 * spending, 2)
    shortfall = max(target - current_balance, 0.0)

    return {
        "transaction_categories": [str(t["category"]) for t in txs],
        "metrics": {
            "months_covered": months,
            "monthly_income": round(income, 2),
            "monthly_spending": round(spending, 2),
            "monthly_surplus": round(surplus, 2),
            "spending_by_category": {str(c): round(v, 2) for c, v in sorted(by_cat.items())},
            "savings_rate": round(savings_rate, 4),
            "debt_to_income": round(dti, 4),
            "total_debt": round(total_debt, 2),
            "current_balance": round(current_balance, 2),
            "emergency_fund_months": round(emergency, 2),
            "discretionary_share": round(discretionary, 4),
        },
        "health_score": {
            "score": score,
            "band": band,
            "components": [
                {"name": n, "value": round(v, 4), "points": round(p, 2), "max_points": mx}
                for n, v, p, mx in components
            ],
        },
        "subscriptions": subscriptions,
        "identified_cuts": identified_cuts,
        "debt_plan": {
            "strategy": "avalanche",
            "payoff_order": [f"{d['lender']} {d['product']}" for d in sorted(DEBTS, key=lambda d: (-d["apr"], d["balance"]))],
            "extra_monthly_payment": extra,
            "months_to_debt_free_current": m_cur,
            "months_to_debt_free_with_extra": m_new,
            "months_saved": m_cur - m_new,
            "interest_saved": round(i_cur - i_new, 2),
        },
        "savings_plan": {
            "monthly_amount": savings_monthly,
            "target_amount": target,
            "months_to_target": math.ceil(shortfall / savings_monthly) if savings_monthly > 0 else None,
        },
    }


# ---------- Document writers ----------


def money(x: float) -> str:
    return f"{x:,.2f}"


def draw_table(page, x0: float, y0: float, widths: list[float], rows: list[list[str]], right_cols: set[int],
               row_h: float = 15, size: float = 8, bold_first: bool = True) -> float:
    shape = page.new_shape()
    xs = [x0]
    for w in widths:
        xs.append(xs[-1] + w)
    for r_i, row in enumerate(rows):
        y = y0 + r_i * row_h
        font = "hebo" if bold_first and r_i == 0 else "helv"
        for c_i, text in enumerate(row):
            if c_i in right_cols and r_i > 0:
                tx = xs[c_i + 1] - 4 - pymupdf.get_text_length(text, fontname=font, fontsize=size)
            else:
                tx = xs[c_i] + 4
            page.insert_text((tx, y + row_h - 4.5), text, fontsize=size, fontname=font)
    y_end = y0 + len(rows) * row_h
    for r_i in range(len(rows) + 1):
        shape.draw_line((xs[0], y0 + r_i * row_h), (xs[-1], y0 + r_i * row_h))
    for x in xs:
        shape.draw_line((x, y0), (x, y_end))
    shape.finish(width=0.5, color=(0, 0, 0))
    shape.commit()
    return y_end


def header(page, lines: list[str], y: float = 50) -> float:
    page.insert_text((40, y), lines[0], fontsize=14, fontname="hebo")
    y += 20
    for line in lines[1:]:
        page.insert_text((40, y), line, fontsize=9, fontname="helv")
        y += 13
    page.insert_text((40, 830), SAMPLE_NOTE, fontsize=7, fontname="helv", color=(0.5, 0.5, 0.5))
    return y + 8


def write_bank_pdf(txs: list[dict], path: Path) -> None:
    doc = pymupdf.open()
    head = ["Date", "Description", "Money out", "Money in", "Balance"]
    widths = [70, 235, 80, 80, 80]
    per_page = 40
    for p_i in range(0, len(txs), per_page):
        page = doc.new_page(width=595, height=842)
        lines = [f"{BANK} - Current Account Statement", f"Account holder: {PERSON}",
                 "IBAN: IE00 NWBK 9999 0000 1234 56 (sample)",
                 "Statement period: 01 Jul 2026 to 30 Sep 2026",
                 f"Opening balance: EUR {money(OPENING_BALANCE)}", f"Page {p_i // per_page + 1}"]
        y = header(page, lines)
        body = [[t["date"].strftime("%d %b %Y"), t["description"],
                 money(-t["amount"]) if t["amount"] < 0 else "",
                 money(t["amount"]) if t["amount"] > 0 else "",
                 money(t["balance"])] for t in txs[p_i:p_i + per_page]]
        draw_table(page, 40, y, widths, [head] + body, right_cols={2, 3, 4})
    doc.save(path)


def write_bank_csv(txs: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Description", "Amount", "Balance"])
        for t in txs:
            w.writerow([t["date"].isoformat(), t["description"], f"{t['amount']:.2f}", f"{t['balance']:.2f}"])


def write_payslip_pdf(path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    y = header(page, ["PAYSLIP", f"Employer: {EMPLOYER}", f"Employee: {PERSON}",
                      "Pay date: 25 Sep 2026", "Pay period: September 2026"])
    rows = [["Description", "Amount (EUR)"], ["Gross Pay", money(PAYSLIP["gross_pay"])]]
    rows += [[k, money(v)] for k, v in PAYSLIP["deductions"].items()]
    rows += [["Net Pay", money(NET_PAY)]]
    draw_table(page, 40, y, [300, 120], rows, right_cols={1}, row_h=18, size=10)
    doc.save(path)


def write_loan_xlsx(debts: list[dict], path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Credit Summary"
    ws.append([f"{BANK} - Credit Summary for {PERSON}"])
    ws.append(["Statement date: 30 Sep 2026", None, None, None, None, None, SAMPLE_NOTE])
    ws.append([])
    ws.append(["Lender", "Product", "Type", "Balance (EUR)", "APR (%)", "Monthly Payment (EUR)", "Remaining Term (months)"])
    for d in debts:
        ws.append([d["lender"], d["product"], d["type"], d["balance"], d["apr"], d["payment"], d.get("term")])
    for col, width in zip("ABCDEFG", (16, 18, 12, 14, 9, 22, 24)):
        ws.column_dimensions[col].width = width
    wb.save(path)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    txs = build_transactions()
    DEBTS[0]["term"] = simulate([DEBTS[0]], 0.0)[0]

    write_bank_pdf(txs, OUT / "bank_statement_jul-sep_2026.pdf")
    write_bank_csv(txs, OUT / "bank_statement_jul-sep_2026.csv")
    write_payslip_pdf(OUT / "payslip_sep_2026.pdf")
    write_loan_xlsx(DEBTS, OUT / "loan_statement_sep_2026.xlsx")

    profile = FinancialProfile.model_validate({
        "transactions": [{k: t[k] for k in ("date", "description", "amount", "balance")} for t in txs],
        "payslips": [{"employee": PERSON, "employer": EMPLOYER, "pay_date": date(2026, 9, 25),
                      "net_pay": NET_PAY, **PAYSLIP}],
        "debts": [{"name": f"{d['lender']} {d['product']}", "kind": d["kind"], "balance": d["balance"],
                   "annual_interest_rate": d["apr"], "monthly_payment": d["payment"],
                   "remaining_term_months": d.get("term")} for d in DEBTS],
        "sources": [
            {"filename": "bank_statement_jul-sep_2026.pdf", "document_type": "bank_statement"},
            {"filename": "payslip_sep_2026.pdf", "document_type": "payslip"},
            {"filename": "loan_statement_sep_2026.xlsx", "document_type": "loan_statement"},
        ],
    })
    (OUT / "expected_profile.json").write_text(profile.model_dump_json(indent=2) + "\n", encoding="utf-8")

    key = answer_key(txs)
    (OUT / "expected.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")

    takeaway = [t for t in txs if t["category"] == Category.TAKEAWAY][:3]
    plan, sav = key["debt_plan"], key["savings_plan"]
    report = Report.model_validate({
        **{k: key[k] for k in ("metrics", "health_score", "subscriptions", "identified_cuts", "debt_plan", "savings_plan")},
        "recommendations": [
            {"agent": "spending", "title": "Halve takeaway spending",
             "detail": f"Takeaway averages EUR {money(key['metrics']['spending_by_category']['takeaway'])}/month. "
                       f"Cutting it in half frees EUR {money(key['identified_cuts'])}/month.",
             "monthly_impact": key["identified_cuts"],
             "evidence": [{k: t[k] for k in ("date", "description", "amount", "balance", "category")} for t in takeaway]},
            {"agent": "debt", "title": f"Pay off the {plan['payoff_order'][0]} first",
             "detail": f"Adding EUR {money(plan['extra_monthly_payment'])}/month makes you debt-free "
                       f"{plan['months_saved']} months earlier and saves EUR {money(plan['interest_saved'])} in interest.",
             "monthly_impact": plan["extra_monthly_payment"]},
            {"agent": "savings", "title": "Build a 3-month emergency fund",
             "detail": f"Save EUR {money(sav['monthly_amount'])}/month to reach EUR {money(sav['target_amount'])} "
                       f"in {sav['months_to_target']} months.",
             "monthly_impact": sav["monthly_amount"]},
        ],
        "llm_used": False,
    })
    (OUT / "mock_report.json").write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"{len(txs)} transactions; score {key['health_score']['score']} ({key['health_score']['band']}); "
          f"debt-free {plan['months_saved']} months earlier; files in {OUT}")


if __name__ == "__main__":
    main()
