"""WealthWise Streamlit entry point. Task C1: docs/specs/03-dashboard-and-rag.md#c1-app-shell-apppy"""

import re
from pathlib import Path

import streamlit as st

from wealthwise.analysis import build_report
from wealthwise.contracts import FinancialProfile, Report, UploadedDocument
from wealthwise.dashboard import render_report
from wealthwise.ingestion import load_profile
from wealthwise.rag import answer_question

SAMPLES = Path(__file__).resolve().parent / "samples"
SAMPLE_FILES = ["bank_statement_jul-sep_2026.pdf", "payslip_sep_2026.pdf", "loan_statement_sep_2026.xlsx"]
MAX_FILES = 5  # per-file size limit is server.maxUploadSize in .streamlit/config.toml


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
st.markdown(
    """
    <style>
        .stApp {
            background: #040b12;
            color: #edf2f7;
        }

        .main .block-container {
            max-width: 1380px;
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }

        [data-testid="stBottom"] {
            position: static !important;
        }

        h1 {
            font-size: 4.2rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.06em !important;
            line-height: 1 !important;
            margin-bottom: 1.5rem !important;
        }

        [data-testid="stWidgetLabel"] {
            font-size: 1.1rem !important;
            color: #edf2f7 !important;
            font-weight: 400 !important;
            margin-bottom: 0.8rem !important;
        }

        .stTextInput .st-bk {
            background: rgba(255, 255, 255, 0.04);
            border-radius: 0.8rem;
        }

        .stTextInput input {
            background: rgba(255, 255, 255, 0.06) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            color: #edf2f7 !important;
            border-radius: 0.75rem !important;
            font-size: 1rem !important;
            min-height: 2.8rem !important;
            padding: 0.6rem 0.9rem !important;
        }

        .stTextInput input::placeholder {
            color: rgba(237, 242, 247, 0.54) !important;
        }

        .stMarkdown p,
        .stWrite p,
        .stAlert p {
            font-size: 1rem !important;
            line-height: 1.5 !important;
            margin: 0 !important;
        }

        .stExpander {
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 0.8rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("WealthWise")
st.caption("Personalised financial guidance from your own documents. Not financial advice.")
st.info(
    "Public demo: please choose **Use sample documents**, or upload fictional files. "
    "Don't upload real financial records."
)

uploads = st.file_uploader(
    f"Upload your bank statement, payslip and loan statement (up to {MAX_FILES} files)",
    type=["pdf", "csv", "xlsx"],
    accept_multiple_files=True,
)
analyse_col, sample_col = st.columns(2)
documents: list[UploadedDocument] | None = None
if analyse_col.button("Analyse", type="primary", disabled=not uploads):
    if len(uploads) > MAX_FILES:
        st.error(f"Please upload at most {MAX_FILES} files.")
    else:
        documents = [UploadedDocument(filename=f.name, content=f.getvalue()) for f in uploads]
if sample_col.button("Use sample documents"):
    documents = [UploadedDocument(filename=n, content=(SAMPLES / n).read_bytes()) for n in SAMPLE_FILES]

if documents:
    for key in ("profile", "report", "demo", "chat_messages", "chat_profile_key", "chat_context"):
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

    render_report(report, profile=profile)

    st.subheader("Ask WealthWise")
    profile_key = profile.model_dump_json()
    if st.session_state.get("chat_profile_key") != profile_key:
        st.session_state.chat_profile_key = profile_key
        st.session_state.chat_messages = []
        st.session_state.chat_context = {"preferences": []}
    st.caption(
        "When AI is enabled, your question and relevant document excerpts may be sent to OpenRouter. "
        "Financial figures are calculated from your data."
    )
    if st.button("Clear chat", key="clear_chat"):
        st.session_state.chat_messages = []
        st.session_state.chat_context = {}
        st.rerun()

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Ask WealthWise about your finances")
    if question:
        st.session_state.chat_messages.append({"role": "user", "content": question})
        if re.search(
            r"\b(?:don't|do not|won't|would rather not)\b.*\b(?:reduce|cut|stop|give up)\b.*\btakeaway\b"
            r"|\btakeaway\b.*\b(?:don't|do not|won't|would rather not)\b.*\b(?:reduce|cut|stop|give up)\b",
            question.lower(),
        ):
            preferences = st.session_state.chat_context.setdefault("preferences", [])
            if "avoid_takeaway_reduction" not in preferences:
                preferences.append("avoid_takeaway_reduction")
        with st.chat_message("user"):
            st.markdown(question)
        try:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = answer_question(
                        profile,
                        report,
                        question,
                        history=st.session_state.chat_messages[-12:],
                        context=st.session_state.chat_context,
                    )
                st.markdown(answer)
            st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        except NotImplementedError:
            st.info("Ask WealthWise is coming soon")
        except Exception as error:
            st.error(f"Ask WealthWise couldn't answer this just now: {error}")
