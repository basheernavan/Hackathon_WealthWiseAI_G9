import io

import openpyxl

from conftest import LOAN_XLSX, sample_bytes
from wealthwise.ingestion.loan_xlsx import parse_loan_xlsx


def test_sample_xlsx_gives_sample_profile_debts(sample_profile):
    debts, warnings = parse_loan_xlsx(sample_bytes(LOAN_XLSX))
    assert debts == sample_profile.debts
    assert warnings == []


def test_not_an_xlsx_gives_a_warning_not_an_exception():
    debts, warnings = parse_loan_xlsx(b"not a spreadsheet")
    assert debts == [] and len(warnings) == 1


def test_sheet_without_header_gives_a_warning():
    wb = openpyxl.Workbook()
    wb.active.append(["Nothing", "here"])
    buf = io.BytesIO()
    wb.save(buf)
    debts, warnings = parse_loan_xlsx(buf.getvalue())
    assert debts == [] and len(warnings) == 1
