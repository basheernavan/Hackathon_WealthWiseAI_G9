"""Task A4: parse the payslip PDF. Spec: docs/specs/01-ingestion.md#a4-payslip-pdf"""

from wealthwise.contracts import Payslip


def parse_payslip_pdf(content: bytes) -> tuple[Payslip | None, list[str]]:
    """Return (payslip, warnings). The payslip is None, with a warning, when it can't be read or doesn't add up."""
    raise NotImplementedError("A4 parse_payslip_pdf")
