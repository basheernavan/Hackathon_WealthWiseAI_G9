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
            background:
                linear-gradient(135deg, #E5F0E5 0%, #F6F9F5 58%, #EEF4ED 100%);
            color: #20352A;
        }

        .main .block-container {
            max-width: 1380px;
            padding: 2.5rem 3rem 3rem;
        }

        [data-testid="stBottom"] {
            position: static !important;
        }

        h1 {
            color: #174D32 !important;
            font-size: clamp(2.8rem, 5vw, 4rem) !important;
            font-weight: 750 !important;
            letter-spacing: -0.045em !important;
            line-height: 1.05 !important;
            margin-bottom: 0.75rem !important;
        }

        h2, h3 {
            color: #205B3B !important;
            letter-spacing: -0.02em;
        }

        [data-testid="stSidebar"] {
            background: #EAF1E9;
            border-right: 1px solid #D3E0D3;
        }

        [data-testid="stWidgetLabel"] {
            color: #294936 !important;
            font-size: 1rem !important;
            font-weight: 550 !important;
            margin-bottom: 0.45rem !important;
        }

        [data-testid="stCaption"] {
            color: #526B58 !important;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stChatInput"] textarea {
            background: #FFFFFF !important;
            border: 1px solid #BDCEBF !important;
            color: #20352A !important;
            border-radius: 0.8rem !important;
            min-height: 2.8rem !important;
            padding: 0.65rem 0.9rem !important;
        }

        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stChatInput"] textarea::placeholder {
            color: #718476 !important;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: rgba(224, 239, 227, 0.78);
            border: 1px dashed #8EAD94;
            border-radius: 1rem;
        }

        [data-testid="stButton"] button {
            border-radius: 0.75rem;
            font-weight: 600;
            transition: border-color 150ms ease, background-color 150ms ease;
        }

        [data-testid="stButton"] button:not([kind="primary"]) {
            background: #FFFFFF;
            border-color: #BDCEBF;
            color: #245B3C;
        }

        [data-testid="stButton"] button:hover {
            border-color: #28734B;
        }

        [data-testid="stAlert"] {
            border-radius: 0.85rem;
        }

        [data-testid="stAlert"] p {
            color: #294936 !important;
        }

        [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.68);
            border: 1px solid #D3E0D3;
            border-radius: 0.85rem;
        }

        .stMarkdown p,
        .stWrite p,
        .stAlert p {
            font-size: 1rem !important;
            line-height: 1.5 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("WealthWise", anchor=False)
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

st.divider()
st.caption(
    "WealthWise is a hackathon pilot and not financial advice. Figures are calculated from the documents "
    "you upload; check them against the originals before acting."
)
