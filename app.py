"""WealthWise Streamlit entry point. Task C1: docs/specs/03-dashboard-and-rag.md#c1-app-shell-apppy"""

import re
from pathlib import Path

import streamlit as st

from wealthwise.analysis import build_report
from wealthwise.contracts import FinancialProfile, Report, UploadedDocument
from wealthwise.dashboard import render_report
from wealthwise.ingestion import load_profile
from wealthwise.rag import answer_question

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "samples"
ASSETS = ROOT / "assets"  # brand sheet: logo lockup, W-leaf icon and robot mascot
LOGO = str(ASSETS / "wealthwise_logo.png")
ICON = str(ASSETS / "wealthwise_icon.png")
ROBOT = str(ASSETS / "wealthwise_robot.png")
SAMPLE_FILES = ["bank_statement_jul-sep_2026.pdf", "payslip_sep_2026.pdf", "loan_statement_sep_2026.xlsx"]
MAX_FILES = 5  # per-file size limit is server.maxUploadSize in .streamlit/config.toml

FEATURES = [
    ("bar_chart", "Understand Your Spending", "Identify top categories and find opportunities to spend less."),
    ("savings", "Build Your Savings", "Get a realistic savings plan and safety net goal."),
    ("credit_card_off", "Reduce Your Debt", "See a clear repayment plan to become debt-free faster."),
    ("forum", "Ask WealthWise", "Ask questions about your finances using your own data."),
]
STEPS = [
    ("upload_file", "Upload Documents", "Bank statements, payslips and loan documents (PDF, CSV, XLSX)."),
    ("settings", "We Analyse", "WealthWise calculates your financial profile from your data."),
    ("lightbulb", "Get Personalised Insights", "Receive your budget, savings strategy and debt repayment plan."),
]
TRUST = [
    ("shield", "Your data stays with you", "Documents are processed in your session and are not saved."),
    ("calculate", "Numbers you can trust", "All financial figures are calculated in code, not by the AI."),
    ("visibility", "Clear and explainable", "See the data behind every insight with transparent recommendations."),
]
ROADMAP = [
    ("account_balance", "Open Banking Integration", "Automatically connect your accounts."),
    ("smartphone", "Mobile App and Voice Coaching", "Take WealthWise everywhere."),
    ("monitoring", "Investment Planning", "Personalised investment insights."),
    ("receipt_long", "Tax Planning Support", "Guidance for better tax decisions."),
]


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


def sample_documents() -> list[UploadedDocument]:
    return [UploadedDocument(filename=n, content=(SAMPLES / n).read_bytes()) for n in SAMPLE_FILES]


def icon_card(key: str, icon: str, title: str, body: str) -> None:
    with st.container(border=True, key=key):
        st.markdown(f"#### :primary[:material/{icon}:]")
        st.markdown(f"**{title}**")
        st.caption(body)


st.set_page_config(page_title="WealthWise", page_icon=ICON, layout="wide")
st.markdown(
    """
    <style>
        .stApp {
            background: #F5F7FA;
            color: #0B2D5B;
        }
        .main .block-container, [data-testid="stMainBlockContainer"] {
            max-width: 1280px;
            padding-top: 3.5rem;
            padding-bottom: 2rem;
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        [data-testid="stBottom"] {
            position: static !important;
        }
        h1, h2, h3 {
            color: #0B2D5B !important;
        }
        a {
            color: #0EA5A0;
        }
        [data-testid="stIconMaterial"] {
            color: #0EA5A0;
        }
        [data-testid="stWidgetLabel"] {
            color: #0B2D5B !important;
        }
        .stTextInput input {
            background: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 0.75rem !important;
        }
        .stExpander, [data-testid="stFileUploaderDropzone"] {
            background: #FFFFFF;
            border-radius: 1rem;
        }
        .stButton button, .ww-button {
            border-radius: 999px !important;
            font-weight: 600 !important;
            padding: 0.45rem 1.4rem !important;
        }

        /* Top bar */
        .st-key-topbar {
            background: #FFFFFF;
            border-radius: 1rem;
            padding: 0.6rem 1.2rem;
            box-shadow: 0 4px 16px rgba(11, 45, 91, 0.05);
        }
        .ww-nav {
            display: flex;
            gap: 1.6rem;
            justify-content: center;
            flex-wrap: wrap;
            font-size: 0.92rem;
        }
        .ww-nav a {
            color: #0B2D5B !important;
            text-decoration: none;
        }
        .ww-nav a:hover {
            color: #0EA5A0 !important;
        }

        /* Hero */
        .ww-pill {
            display: inline-block;
            background: #E6F2FF;
            color: #0B2D5B;
            border-radius: 999px;
            padding: 0.25rem 0.9rem;
            font-size: 0.82rem;
        }
        .ww-hero {
            font-size: clamp(2.3rem, 5vw, 3.6rem);
            font-weight: 700;
            line-height: 1.08;
            color: #0B2D5B;
            margin: 1rem 0 0.8rem;
            letter-spacing: -0.02em;
        }
        .ww-hero, .ww-hero span {
            color: #0B2D5B !important;
        }
        .ww-hero .ww-accent {
            color: #22C55E !important;
            font-style: normal;
        }
        .ww-lead {
            font-size: 1.08rem;
            color: #475569;
            max-width: 34rem;
        }
        .ww-button {
            display: inline-block;
            border: 1px solid #0EA5A0;
            color: #0B2D5B !important;
            background: #FFFFFF;
            text-decoration: none !important;
        }
        .st-key-hero-robot img {
            filter: drop-shadow(0 18px 30px rgba(11, 45, 91, 0.18));
        }
        [class*="st-key-doc-"] {
            background: #FFFFFF;
            border-color: #E2E8F0 !important;
            border-radius: 0.9rem;
            box-shadow: 0 4px 14px rgba(11, 45, 91, 0.06);
        }

        /* Cards */
        [class*="st-key-feature-"], [class*="st-key-step-"] {
            background: #FFFFFF;
            border-color: #E2E8F0 !important;
            border-radius: 1rem;
            min-height: 170px;
        }
        [class*="st-key-feature-"] [data-testid="stIconMaterial"],
        [class*="st-key-step-"] [data-testid="stIconMaterial"],
        [class*="st-key-trust-"] [data-testid="stIconMaterial"] {
            font-size: 2rem;
        }
        .st-key-trust {
            background: #E6F2FF;
            border-radius: 1rem;
            padding: 1.2rem 1.4rem;
        }
        .ww-step {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            background: #0EA5A0;
            color: #FFFFFF;
            font-weight: 700;
        }

        /* Roadmap */
        .st-key-roadmap {
            background: linear-gradient(120deg, #0B2D5B, #0E6E7E);
            border-radius: 1rem;
            padding: 1.4rem 1.6rem;
        }
        .st-key-roadmap, .st-key-roadmap h3, .st-key-roadmap p,
        .st-key-roadmap [data-testid="stCaptionContainer"],
        .st-key-roadmap [data-testid="stIconMaterial"] {
            color: #FFFFFF !important;
        }
        .ww-coming {
            float: right;
            background: #0EA5A0;
            color: #FFFFFF;
            border-radius: 999px;
            padding: 0.3rem 1rem;
            font-size: 0.85rem;
            font-weight: 600;
        }

        /* Documents read */
        .ww-chip {
            display: inline-block;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 999px;
            padding: 0.25rem 0.8rem;
            margin: 0 0.4rem 0.4rem 0;
            font-size: 0.88rem;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #FFFFFF;
        }
        .ww-side a {
            display: block;
            color: #0B2D5B !important;
            text-decoration: none;
            padding: 0.55rem 0.8rem;
            border-radius: 0.6rem;
            margin-bottom: 0.2rem;
        }
        .ww-side a:hover, .ww-side a:first-child {
            background: #E6F2FF;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Streamlit sets the URL hash on in-page links but doesn't scroll, so the nav links scroll themselves.
st.html(
    """<script>
    if (!window.wwNav) {
        window.wwNav = true;
        document.addEventListener("click", (event) => {
            const link = event.target.closest('a[href^="#"]');
            const target = link && document.getElementById(link.getAttribute("href").slice(1));
            if (target) {
                event.preventDefault();
                target.scrollIntoView({block: "start"});
            }
        });
    }
    </script>""",
    unsafe_allow_javascript=True,
)

has_report = "report" in st.session_state
documents: list[UploadedDocument] | None = None

if has_report:
    with st.sidebar:
        st.image(LOGO, width=200)
        st.markdown(
            '<nav class="ww-side">'
            '<a href="#dashboard">Dashboard</a>'
            '<a href="#spending">Spending</a>'
            '<a href="#recommendations">Savings</a>'
            '<a href="#debt">Debt</a>'
            '<a href="#ask-wealthwise">Ask WealthWise</a>'
            '<a href="#upload">Upload Documents</a>'
            "</nav>",
            unsafe_allow_html=True,
        )

with st.container(key="topbar"):
    logo_col, nav_col, action_col = st.columns([3, 6, 2], vertical_alignment="center")
    logo_col.image(LOGO, width=230)
    if has_report:
        nav_col.markdown(
            '<div class="ww-nav"><a href="#dashboard">Dashboard</a><a href="#spending">Spending</a>'
            '<a href="#recommendations">Recommendations</a><a href="#ask-wealthwise">Ask WealthWise</a></div>',
            unsafe_allow_html=True,
        )
        action_col.markdown('<a class="ww-button" href="#upload">Upload Documents</a>', unsafe_allow_html=True)
    else:
        nav_col.markdown(
            '<div class="ww-nav"><a href="#features">Features</a><a href="#how-it-works">How it works</a>'
            '<a href="#trust">Trust &amp; Security</a><a href="#roadmap">Roadmap</a></div>',
            unsafe_allow_html=True,
        )
        if action_col.button("Try Demo", type="primary", key="try_demo_top"):
            documents = sample_documents()
st.caption("WealthWise: personalised financial guidance from your own documents. Not financial advice.")

if not has_report:
    text_col, art_col = st.columns([6, 5], vertical_alignment="center")
    with text_col:
        st.markdown(
            '<span class="ww-pill">AI-Powered &nbsp;•&nbsp; Private &nbsp;•&nbsp; '
            "Built for a brighter financial future</span>"
            '<h1 class="ww-hero">Make your money <em class="ww-accent">make more sense.</em></h1>'
            '<p class="ww-lead">Upload your financial documents and get personalised insights on spending, '
            "savings and debt, powered by AI but grounded in your own data.</p>",
            unsafe_allow_html=True,
        )
        demo_col, upload_link_col = st.columns(2)
        if demo_col.button("Try the Demo", type="primary", key="try_demo_hero"):
            documents = sample_documents()
        upload_link_col.markdown('<a class="ww-button" href="#upload">Upload your documents</a>', unsafe_allow_html=True)
        for column, (icon, text) in zip(
            st.columns(3),
            [
                ("verified", "No sign-up needed (for demo)"),
                ("lock", "Your data stays private (in this session)"),
                ("task_alt", "Clear, actionable recommendations"),
            ],
        ):
            column.caption(f":primary[:material/{icon}:] {text}")
    with art_col:
        robot_col, docs_col = st.columns([1, 1], vertical_alignment="center")
        with robot_col.container(key="hero-robot"):
            st.image(ROBOT, width=200)
        with docs_col:
            for key, icon, title in [
                ("doc-bank", "account_balance", "Bank Statement"),
                ("doc-payslip", "description", "Payslip"),
                ("doc-loan", "percent", "Loan Document"),
            ]:
                with st.container(border=True, key=key):
                    st.markdown(f":primary[:material/{icon}:] **{title}**")
                    st.caption("PDF, CSV, XLSX")

    st.subheader("Features", anchor="features")
    for index, (column, (icon, title, body)) in enumerate(zip(st.columns(4), FEATURES)):
        with column:
            icon_card(f"feature-{index}", icon, title, body)

    st.subheader("How it works", anchor="how-it-works")
    for index, (column, (icon, title, body)) in enumerate(zip(st.columns(3), STEPS), start=1):
        with column.container(border=True, key=f"step-{index}"):
            st.markdown(f'<span class="ww-step">{index}</span>', unsafe_allow_html=True)
            st.markdown(f"#### :primary[:material/{icon}:]")
            st.markdown(f"**{title}**")
            st.caption(body)

    with st.container(key="trust"):
        st.subheader("Built with trust and transparency", anchor="trust")
        for index, (column, (icon, title, body)) in enumerate(zip(st.columns(3), TRUST)):
            with column.container(key=f"trust-{index}"):
                st.markdown(f"#### :primary[:material/{icon}:]")
                st.markdown(f"**{title}**")
                st.caption(body)

st.markdown('<div id="upload"></div>', unsafe_allow_html=True)
with st.expander("Upload your documents", expanded=not has_report, icon=":material/upload_file:"):
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
    if analyse_col.button("Analyse", type="primary", disabled=not uploads):
        if len(uploads) > MAX_FILES:
            st.error(f"Please upload at most {MAX_FILES} files.")
        else:
            documents = [UploadedDocument(filename=f.name, content=f.getvalue()) for f in uploads]
    if sample_col.button("Use sample documents"):
        documents = sample_documents()

if documents:
    for key in ("profile", "report", "demo", "chat_messages", "chat_profile_key", "chat_context"):
        st.session_state.pop(key, None)
    try:
        with st.spinner("Reading your documents..."):
            run_pipeline(documents)
    except Exception as e:
        st.error(f"Could not analyse these documents: {e}")
    else:
        st.session_state.show_dashboard = True
        st.rerun()  # redraw with the dashboard layout (sidebar, report nav)

if not has_report:
    with st.container(key="roadmap"):
        st.markdown('<span class="ww-coming">Coming next</span>', unsafe_allow_html=True)
        st.subheader("Future roadmap", anchor="roadmap")
        st.caption("Building towards a more complete financial companion.")
        for column, (icon, title, body) in zip(st.columns(4), ROADMAP):
            column.markdown(f"#### :material/{icon}:")
            column.markdown(f"**{title}**")
            column.caption(body)

if has_report:
    profile: FinancialProfile = st.session_state.profile
    report: Report = st.session_state.report
    st.header("Your financial health")
    st.caption("Let's make a plan for your money.")
    if st.session_state.demo:
        st.badge("Demo data", icon=":material/science:", color="orange")

    st.subheader(f"{len(profile.sources)} documents read")
    st.markdown(
        "".join(
            f'<span class="ww-chip">{source.filename} · {source.document_type.value.replace("_", " ")}</span>'
            for source in profile.sources
        ),
        unsafe_allow_html=True,
    )
    for source in profile.sources:
        for warning in source.warnings:
            st.warning(f"{source.filename}: {warning}")

    render_report(report, profile=profile)
    if st.session_state.pop("show_dashboard", False):
        # The chat input pulls the page to the bottom; start a fresh report at the score instead.
        st.html(
            """<script>setTimeout(() => document.getElementById("dashboard")?.scrollIntoView({block: "start"}), 600);</script>""",
            unsafe_allow_javascript=True,
        )

    st.subheader("Ask WealthWise", anchor="ask-wealthwise")
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
        with st.chat_message(message["role"], avatar=ROBOT if message["role"] == "assistant" else None):
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
            with st.chat_message("assistant", avatar=ROBOT):
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
