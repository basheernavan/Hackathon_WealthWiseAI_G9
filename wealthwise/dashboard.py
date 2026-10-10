"""Task C2: render a Report in Streamlit, plus money/percent formatting. Spec: docs/specs/03-dashboard-and-rag.md#c2-report-view

app.py (task C1) calls render_report; this placeholder keeps the app running until C2 is built.
"""

import streamlit as st

from wealthwise.contracts import Report


def format_eur(amount: float) -> str:
    """1234.5 -> '€1,234.50'; -12 -> '-€12.00'."""
    raise NotImplementedError("C2 format_eur")


def format_pct(fraction: float) -> str:
    """0.0681 -> '6.8%'."""
    raise NotImplementedError("C2 format_pct")


def render_report(report: Report) -> None:
    st.info(f"Report view not built yet (task C2). Health Score: {report.health_score.score}")
