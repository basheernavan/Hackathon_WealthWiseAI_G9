from test_data_jan import JAN_LOAN_PDF, jan_bytes
from test_detect import pdf_with_text
from wealthwise.contracts import Debt, DebtKind
from wealthwise.ingestion.loan_pdf import parse_loan_pdf


def test_loan_pdf_gives_one_debt():
    debts, warnings = parse_loan_pdf(jan_bytes(JAN_LOAN_PDF))
    assert warnings == []
    assert debts == [
        Debt(name="AIB Personal Loan", kind=DebtKind.LOAN, balance=18450, annual_interest_rate=7.2, monthly_payment=345, remaining_term_months=60)
    ]


def test_pdf_missing_fields_gives_a_warning():
    debts, warnings = parse_loan_pdf(pdf_with_text("SOME LOAN\nInterest Rate: 5%"))
    assert debts == [] and len(warnings) == 1
