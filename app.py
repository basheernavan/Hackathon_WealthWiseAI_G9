"""WealthWise Streamlit entry point. Stream C owns this file: docs/specs/03-dashboard-and-rag.md"""

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
