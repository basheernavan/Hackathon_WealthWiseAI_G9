"""WealthWise Streamlit entry point. Task C1: docs/specs/03-dashboard-and-rag.md#c1-app-shell-apppy"""

import streamlit as st

st.set_page_config(page_title="WealthWise", layout="wide")
st.title("WealthWise")
st.caption("Personalised financial guidance from your own documents. Not financial advice.")

st.file_uploader(
    "Upload your bank statement, payslip and loan statement",
    type=["pdf", "csv", "xlsx"],
    accept_multiple_files=True,
)
st.info("Dashboard under construction.")
