"""WealthWise Streamlit entry point. Task C1: docs/specs/03-dashboard-and-rag.md#c1-app-shell-apppy"""

from pathlib import Path

import streamlit as st

from wealthwise.analysis import build_report
from wealthwise.contracts import FinancialProfile, Report, UploadedDocument
from wealthwise.dashboard import render_report
from wealthwise.ingestion import load_profile
from wealthwise.rag import answer_question

SAMPLES = Path(__file__).resolve().parent / "samples"
SAMPLE_FILES = ["bank_statement_jul-sep_2026.pdf", "payslip_sep_2026.pdf", "loan_statement_sep_2026.xlsx"]


def run_pipeline(documents: list[UploadedDocument]) -> None:
    """Store profile and report in session state; fall back to sample answers while a stream is unbuilt."""
    demo = False
    try:
        profile = load_profile(documents)
    except NotImplementedError:
        profile = FinancialProfile.model_validate_json((SAMPLES / "expected_profile.json").read_text(encoding="utf-8"))
        demo = True
    try:
        report = build_report(profile)
    except NotImplementedError:
        report = Report.model_validate_json((SAMPLES / "mock_report.json").read_text(encoding="utf-8"))
        demo = True
    st.session_state.update(profile=profile, report=report, demo=demo)


st.set_page_config(page_title="WealthWise", layout="wide")
st.title("WealthWise")
st.caption("Personalised financial guidance from your own documents. Not financial advice.")

uploads = st.file_uploader(
    "Upload your bank statement, payslip and loan statement",
    type=["pdf", "csv", "xlsx"],
    accept_multiple_files=True,
)
analyse_col, sample_col = st.columns(2)
documents: list[UploadedDocument] | None = None
if analyse_col.button("Analyse", type="primary", disabled=not uploads):
    documents = [UploadedDocument(filename=f.name, content=f.getvalue()) for f in uploads]
if sample_col.button("Use sample documents"):
    documents = [UploadedDocument(filename=n, content=(SAMPLES / n).read_bytes()) for n in SAMPLE_FILES]

if documents:
    for key in ("profile", "report", "demo"):
        st.session_state.pop(key, None)
    try:
        with st.spinner("Reading your documents..."):
            run_pipeline(documents)
    except Exception as e:
        st.error(f"Could not analyse these documents: {e}")

if "report" in st.session_state:
    profile: FinancialProfile = st.session_state.profile
    report: Report = st.session_state.report
    if st.session_state.demo:
        st.badge("Demo data", icon=":material/science:", color="orange")

    st.subheader(f"{len(profile.sources)} documents read")
    for source in profile.sources:
        st.markdown(f"**{source.filename}**: {source.document_type.value.replace('_', ' ')}")
        for warning in source.warnings:
            st.warning(f"{source.filename}: {warning}")

    render_report(report)

    st.subheader("Ask WealthWise")
    question = st.text_input("Ask a question about your finances", placeholder="How much do I spend on takeaway?")
    if question:
        try:
            with st.spinner("Thinking..."):
                st.write(answer_question(profile, report, question))
        except NotImplementedError:
            st.info("Ask WealthWise is coming soon")
