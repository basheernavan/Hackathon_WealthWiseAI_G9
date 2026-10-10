"""C1 app shell, driven headless with Streamlit's AppTest."""

from streamlit.testing.v1 import AppTest


def run_app() -> AppTest:
    return AppTest.from_file("../app.py", default_timeout=60).run()


def test_page_shows_header_and_disclaimer():
    at = run_app()
    assert at.title[0].value == "WealthWise"
    assert "Not financial advice" in at.caption[0].value
    assert not at.exception


def test_sample_documents_produce_a_report_without_errors(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    at = run_app()
    next(b for b in at.button if b.label == "Use sample documents").click().run()
    assert not at.exception
    assert not at.error
    assert "report" in at.session_state and "profile" in at.session_state
    assert any("documents read" in h.value for h in at.subheader)
