"""Stream A: turn uploaded files into a FinancialProfile. Spec: docs/specs/01-ingestion.md

Task A6 builds load_profile: detect each file's type, call the matching parser, and combine the results.
The parsers live in their own modules (tasks A1-A5); call them through this module's names, e.g.
`bank_csv.parse_bank_csv(...)`, so A6's tests can monkeypatch them before they are built.
"""

from pathlib import PurePath

from wealthwise.contracts import DocumentType, FinancialProfile, SourceDocument, UploadedDocument
from wealthwise.ingestion import bank_csv, bank_pdf, detect, loan_pdf, loan_xlsx, payslip_pdf  # noqa: F401


def load_profile(documents: list[UploadedDocument]) -> FinancialProfile:
    profile = FinancialProfile()
    statement_ranges = []  # (first date, last date, filename) of each bank statement kept so far
    for document in documents:
        extension = PurePath(document.filename).suffix.lower()
        document_type = detect.detect_document_type(document.filename, document.content)
        warnings: list[str] = []

        if document_type is None:
            document_type = DocumentType.LOAN_STATEMENT if extension == ".xlsx" else DocumentType.BANK_STATEMENT
            warnings.append("Could not recognise document type")
        elif document_type == DocumentType.BANK_STATEMENT:
            parse = bank_csv.parse_bank_csv if extension == ".csv" else bank_pdf.parse_bank_pdf
            transactions, warnings = parse(document.content)
            if transactions:
                first, last = min(t.date for t in transactions), max(t.date for t in transactions)
                overlap = next((name for start, end, name in statement_ranges if first <= end and start <= last), None)
                if overlap:
                    warnings = [*warnings, f"Overlaps {overlap}; ignored"]
                else:
                    statement_ranges.append((first, last, document.filename))
                    profile.transactions.extend(transactions)
        elif document_type == DocumentType.PAYSLIP:
            payslip, warnings = payslip_pdf.parse_payslip_pdf(document.content)
            if payslip:
                profile.payslips.append(payslip)
        else:
            parse = loan_pdf.parse_loan_pdf if extension == ".pdf" else loan_xlsx.parse_loan_xlsx
            debts, warnings = parse(document.content)
            profile.debts.extend(debts)

        profile.sources.append(SourceDocument(filename=document.filename, document_type=document_type, warnings=warnings))

    if not (profile.transactions or profile.payslips or profile.debts):
        raise ValueError("No supported documents")
    profile.transactions.sort(key=lambda t: t.date)  # stable: same-day rows keep statement order
    return profile
