from conftest import PAYSLIP_PDF, sample_bytes
from test_data_jan import JAN_PAYSLIP_PDF, jan_bytes
from test_detect import pdf_with_text
from wealthwise.ingestion.payslip_pdf import parse_payslip_pdf


def test_sample_payslip_gives_sample_profile_payslip(sample_profile):
    payslip, warnings = parse_payslip_pdf(sample_bytes(PAYSLIP_PDF))
    assert warnings == []
    assert payslip == sample_profile.payslips[0]


def test_line_based_payslip_is_read():
    payslip, warnings = parse_payslip_pdf(jan_bytes(JAN_PAYSLIP_PDF))
    assert warnings == []
    assert (payslip.employer, payslip.employee, str(payslip.pay_date)) == ("ABC TECHNOLOGY LTD", "John Murphy", "2026-01-31")
    assert (payslip.gross_pay, payslip.net_pay) == (4200.0, 3272.0)
    assert payslip.deductions == {"Income Tax": 520.0, "PRSI": 168.0, "USC": 120.0, "Pension": 120.0}


def test_pdf_that_is_not_a_payslip_gives_none_and_a_warning():
    payslip, warnings = parse_payslip_pdf(pdf_with_text("Dear customer, thank you."))
    assert payslip is None and len(warnings) == 1


def test_payslip_that_does_not_add_up_gives_none_and_a_warning():
    text = "Employer: X Ltd\nEmployee: A B\nPay date: 25 Sep 2026\nGross Pay: EUR 100.00\nTax: EUR 10.00\nNet Pay: EUR 50.00"
    payslip, warnings = parse_payslip_pdf(pdf_with_text(text))
    assert payslip is None and len(warnings) == 1
