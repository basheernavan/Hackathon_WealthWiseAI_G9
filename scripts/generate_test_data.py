"""Write the scenario folders in test_data/ (fictional people only). Run: python scripts/generate_test_data.py

Same layouts as test_data/jan_2026/: text-line bank and payslip PDFs, loan as PDF or XLSX, CSV with unsigned amounts.
Each scenario aims at a different part of the Financial Health Score (see wealthwise/analysis/score.py).
"""

from pathlib import Path

import openpyxl
import pymupdf

ROOT = Path(__file__).resolve().parents[1] / "test_data"


def eur(x: float) -> str:
    return f"EUR {x:,.2f}"


def write_pdf(path: Path, lines: list[str]) -> None:
    doc = pymupdf.open()
    page, y = doc.new_page(), 60
    for line in lines:
        if y > 780:
            page, y = doc.new_page(), 60
        page.insert_text((50, y), line, fontsize=10)
        y += 14
    doc.save(path)


def bank_pdf(path, bank, holder, start, end, opening, txns):
    """txns: (dd/mm/yyyy, description, 'Credit'|'Debit', amount). Closing balance is printed correctly unless `txns` says otherwise."""
    balance = opening
    for _, _, direction, amount in txns:
        balance += amount if direction == "Credit" else -amount
    lines = [bank.upper(), f"Account Holder: {holder}", "Account Number: 40112233", f"Statement Period: {start} - {end}",
             f"Opening Balance: {eur(opening)}", "Transactions"]
    lines += [f"{d} {desc} {dirn} {eur(a)}" for d, desc, dirn, a in txns]
    lines.append(f"Closing Balance: {eur(balance)}")
    write_pdf(path, lines)


def payslip_pdf(path, employer, employee, pay_date, gross, tax, prsi, usc, pension):
    net = round(gross - tax - prsi - usc - pension, 2)
    write_pdf(path, [employer.upper(), f"Employee: {employee}", "Employee ID: EMP2001", f"Pay Date: {pay_date}",
                     f"Gross Salary: {eur(gross)}", f"Income Tax: {eur(tax)}", f"PRSI: {eur(prsi)}", f"USC: {eur(usc)}",
                     f"Pension: {eur(pension)}", f"Net Pay: {eur(net)}"])
    return net


def loan_pdf(path, lender, borrower, original, balance, rate, payment, term):
    write_pdf(path, [f"{lender.upper()} PERSONAL LOAN", f"Borrower: {borrower}", "Loan Number: PL100200",
                     f"Original Loan Amount: EUR {original:,}", f"Current Balance: EUR {balance:,}", f"Interest Rate: {rate}%",
                     f"Monthly Repayment: EUR {payment:,}", f"Remaining Term: {term} Months", "Next Payment Date: 15 of next month"])


def loan_xlsx(path, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Lender", "Product", "Type", "Balance (EUR)", "APR (%)", "Monthly Payment (EUR)", "Remaining Term (months)"])
    for r in rows:
        ws.append(r)
    wb.save(path)


def month_txns(m, rent=None, groceries=(), eating=(), transport=(), utilities=(), subs=(), shopping=(), fun=(), debt=(), salary=0.0, extra=()):
    """One month of transactions for month number m (2026). Each group is a list of (description, amount)."""
    t = [(f"01/{m:02d}/2026", "Monthly Salary Credit", "Credit", salary)] if salary else []
    day = 2
    if rent:
        t.append((f"{day:02d}/{m:02d}/2026", "Rent Payment", "Debit", rent))
    for group in (groceries, eating, transport, utilities, subs, shopping, fun, debt, extra):
        for desc, amount in group:
            day = day % 27 + 1
            t.append((f"{day:02d}/{m:02d}/2026", desc, "Debit", amount))
    return sorted(t, key=lambda x: x[0])


def folder(name):
    p = ROOT / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def main():
    # 1. Best case: high savings, no debt, big cushion, little discretionary spend. Expect ~100 / good.
    p = folder("best_saver_mar_2026")
    net = payslip_pdf(p / "Payslip_March_2026.pdf", "Harbour Software Ltd", "Aoife Brennan", "31 March 2026", 6500, 1300, 260, 190, 325)
    bank_pdf(p / "Bank_Statement_March_2026.pdf", "Bank of Ireland", "Aoife Brennan", "01 March 2026", "31 March 2026", 14200.00,
             month_txns(3, salary=net, rent=1150, groceries=[("Tesco Grocery", 210), ("Lidl", 95)], transport=[("Leap Card", 60)],
                        utilities=[("Utility Bill", 120)], subs=[("Netflix Subscription", 13.99)], eating=[("Restaurant", 45)]))

    # 2. Good: small manageable loan, healthy savings, adequate cushion. Expect good.
    p = folder("good_small_loan_apr_2026")
    net = payslip_pdf(p / "Payslip_April_2026.pdf", "Corrib Engineering Ltd", "Conor Walsh", "30 April 2026", 4800, 900, 192, 140, 240)
    bank_pdf(p / "Bank_Statement_April_2026.pdf", "AIB", "Conor Walsh", "01 April 2026", "30 April 2026", 4200.00,
             month_txns(4, salary=net, rent=1250, groceries=[("Dunnes", 260), ("Aldi", 90)], transport=[("Petrol", 110)],
                        utilities=[("Utility Bill", 140)], subs=[("Spotify Subscription", 10.99)], eating=[("Starbucks", 38), ("Restaurant", 60)],
                        shopping=[("Amazon", 75)], debt=[("Loan Repayment", 150)]))
    loan_pdf(p / "Car_Loan_Statement.pdf", "Permanent TSB", "Conor Walsh", 6000, 3600, 6.5, 150, 26)

    # 3. In between: some savings, moderate debt, thin cushion, mixed spending. Expect fair.
    p = folder("average_mixed_may_2026")
    net = payslip_pdf(p / "Payslip_May_2026.pdf", "Lakeside Retail Group", "Niamh Doyle", "31 May 2026", 3900, 650, 156, 110, 100)
    bank_pdf(p / "Bank_Statement_May_2026.pdf", "Bank of Ireland", "Niamh Doyle", "01 May 2026", "31 May 2026", 1500.00,
             month_txns(5, salary=net, rent=1250, groceries=[("Tesco Grocery", 300)], transport=[("Leap Card", 90)],
                        utilities=[("Utility Bill", 160)], subs=[("Netflix Subscription", 17.99), ("Spotify Subscription", 10.99)],
                        eating=[("Deliveroo", 80), ("Restaurant", 90)], shopping=[("Zara", 90)], fun=[("Cinema", 25)],
                        debt=[("Loan Repayment", 420)]))
    loan_pdf(p / "Personal_Loan_Statement.pdf", "Bank of Ireland", "Niamh Doyle", 12000, 8800, 8.9, 220, 44)

    # 4. Worst case: spends more than earned, heavy credit card and loan, overdrawn-ish. Expect ~0 / needs attention.
    p = folder("worst_overspender_jun_2026")
    net = payslip_pdf(p / "Payslip_June_2026.pdf", "City Call Centre Ltd", "Darragh Kelly", "30 June 2026", 2200, 300, 88, 50, 0)
    bank_pdf(p / "Bank_Statement_June_2026.pdf", "AIB", "Darragh Kelly", "01 June 2026", "30 June 2026", 180.00,
             month_txns(6, salary=net, rent=1100, groceries=[("Tesco Grocery", 160)], transport=[("Petrol", 90)],
                        utilities=[("Utility Bill", 150)], subs=[("Netflix Subscription", 17.99), ("Disney Subscription", 11.99), ("Gym Membership", 45)],
                        eating=[("Deliveroo", 120), ("Just Eat", 85), ("Restaurant", 90)], shopping=[("Amazon", 210), ("Penneys", 95)],
                        fun=[("Pub", 130), ("Ticketmaster", 110)], debt=[("Credit Card Payment", 200), ("Loan Repayment", 420)]))
    loan_xlsx(p / "Loan_Statement_June_2026.xlsx", [
        ["AIB", "Credit Card", "Credit Card", 6400, 21.9, 200, None],
        ["Credit Union", "Personal Loan", "Loan", 9000, 12.5, 420, 24],
    ])

    # 5. Debt-to-income above 50%: income fine, repayments swallow it. Debt component = 0, others fair.
    p = folder("high_debt_burden_jul_2026")
    net = payslip_pdf(p / "Payslip_July_2026.pdf", "Westside Logistics Ltd", "Ciara Moran", "31 July 2026", 4200, 720, 168, 120, 0)
    bank_pdf(p / "Bank_Statement_July_2026.pdf", "Bank of Ireland", "Ciara Moran", "01 July 2026", "31 July 2026", 2600.00,
             month_txns(7, salary=net, rent=0, groceries=[("Supervalu", 170)], transport=[("Circle K", 60)],
                        utilities=[("Electric Ireland", 100)], eating=[("Starbucks", 20)],
                        debt=[("Loan Repayment", 900), ("Credit Card Payment", 1300)]))
    loan_xlsx(p / "Loan_Statement_July_2026.xlsx", [
        ["Bank of Ireland", "Home Improvement Loan", "Loan", 41000, 7.9, 900, 52],
        ["Bank of Ireland", "Platinum Card", "Credit Card", 14500, 19.9, 1300, None],
    ])

    # 6. No emergency fund: saves well but the balance is almost empty. Emergency component ~0, savings full.
    p = folder("no_emergency_fund_aug_2026")
    net = payslip_pdf(p / "Payslip_August_2026.pdf", "Bluebell Dental Clinic", "Sean Gallagher", "31 August 2026", 4000, 680, 160, 110, 50)
    bank_pdf(p / "Bank_Statement_August_2026.pdf", "Bank of Ireland", "Sean Gallagher", "01 August 2026", "31 August 2026", 0.00,
             month_txns(8, salary=net, rent=1000, groceries=[("Lidl", 150), ("Tesco Grocery", 90)], transport=[("Irish Rail", 80)],
                        utilities=[("Utility Bill", 110)], eating=[("Restaurant", 40)], subs=[("Spotify Subscription", 10.99)],
                        extra=[("Transfer to Savings", 1200)]))

    # 7. High discretionary share: takeaways, shopping, nights out. Savings and cushion fine, discretionary component 0.
    p = folder("high_discretionary_sep_2026")
    net = payslip_pdf(p / "Payslip_September_2026.pdf", "Pixel Studio Ltd", "Ella Fitzgerald", "30 September 2026", 5200, 1000, 208, 150, 130)
    bank_pdf(p / "Bank_Statement_September_2026.pdf", "AIB", "Ella Fitzgerald", "01 September 2026", "30 September 2026", 9000.00,
             month_txns(9, salary=net, rent=1000, groceries=[("Tesco Grocery", 100)], transport=[("Uber", 70)],
                        utilities=[("Utility Bill", 90)], eating=[("Deliveroo", 160), ("Uber Eats", 120), ("Restaurant", 150), ("Starbucks", 60)],
                        shopping=[("Zara", 180), ("Amazon", 140)], fun=[("Brazen Head", 140), ("Cineworld", 40), ("Ticketmaster", 120)],
                        subs=[("Netflix Subscription", 17.99)]))

    # 8. Subscription creep: three months in one statement, the same five subscriptions every month.
    p = folder("subscription_creep_q1_2026")
    net = payslip_pdf(p / "Payslip_March_2026.pdf", "Greenfield Council", "Mairead Quinn", "31 March 2026", 4000, 680, 160, 110, 150)
    txns, balance_in = [], 3000.00
    for m in (1, 2, 3):
        txns += month_txns(m, salary=net, rent=1000, groceries=[("Aldi", 200)], utilities=[("Utility Bill", 120)], transport=[("Petrol", 70)],
                           subs=[("Netflix Subscription", 17.99), ("Spotify Subscription", 10.99), ("Disney Subscription", 9.99),
                                 ("Flyefit Gym", 29.99), ("Gym Membership", 55.00)])
    bank_pdf(p / "Bank_Statement_Jan-Mar_2026.pdf", "Bank of Ireland", "Mairead Quinn", "01 January 2026", "31 March 2026", balance_in, txns)

    # 9. No debt files at all and no payslip: bank statement only. Debt plan must be None; debt component full marks.
    p = folder("bank_only_no_debt_oct_2026")
    bank_pdf(p / "Bank_Statement_October_2026.pdf", "Bank of Ireland", "Tadhg Lynch", "01 October 2026", "31 October 2026", 3800.00,
             month_txns(10, salary=3400, rent=1100, groceries=[("Tesco Grocery", 220)], transport=[("Leap Card", 55)],
                        utilities=[("Utility Bill", 125)], eating=[("Restaurant", 70), ("Starbucks", 25)], subs=[("Netflix Subscription", 17.99)],
                        shopping=[("Amazon", 60)], fun=[("Pub", 50)]))

    # 10. Messy inputs: unsigned CSV only, unknown merchants (category other), a refund, no loan, no payslip.
    p = folder("messy_csv_only_nov_2026")
    rows = [("2026-11-01", "Salary", 2900), ("2026-11-02", "Rent", 950), ("2026-11-03", "Groceries", 160.25), ("2026-11-05", "Netflix", 17.99),
            ("2026-11-07", "Pub", 64), ("2026-11-09", "Joe's Hardware", 88.4), ("2026-11-12", "ACME Dental", 120), ("2026-11-14", "Refund", 35),
            ("2026-11-18", "Petrol", 70), ("2026-11-21", "Restaurant", 55), ("2026-11-27", "Mystery Transfer", 300)]
    (p / "transactions_nov_2026.csv").write_text("Date,Category,Amount\n" + "\n".join(f"{d},{c},{a}" for d, c, a in rows) + "\n", encoding="utf-8")
    # 11. A statement whose printed closing balance is wrong on purpose, to check the mismatch warning.
    p = folder("wrong_closing_balance_nov_2026")
    write_pdf(p / "Bank_Statement_November_2026_wrong_closing.pdf", [
        "AIB", "Account Holder: Pat Nolan", "Statement Period: 01 November 2026 - 30 November 2026", "Opening Balance: EUR 500.00",
        "Transactions", "01/11/2026 Monthly Salary Credit EUR 2,900.00", "02/11/2026 Rent Payment Debit EUR 950.00",
        "05/11/2026 Tesco Grocery Debit EUR 160.25", "Closing Balance: EUR 9,999.99"])


if __name__ == "__main__":
    main()
