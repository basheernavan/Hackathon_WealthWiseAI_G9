"""C1 app shell, driven headless with Streamlit's AppTest."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from wealthwise.contracts import Report
import wealthwise.rag as rag


def run_app() -> AppTest:
    return AppTest.from_file("../app.py", default_timeout=120).run()


def test_page_shows_header_and_disclaimer():
    at = run_app()
    assert at.title[0].value == "WealthWise"
    assert "Not financial advice" in at.caption[0].value
    assert not at.exception


def test_page_warns_visitors_to_use_sample_documents():
    at = run_app()
    assert any("sample documents" in info.value and "real" in info.value for info in at.info)


def test_upload_size_is_limited_in_streamlit_config():
    import tomllib

    config = tomllib.loads((Path(__file__).resolve().parents[1] / ".streamlit" / "config.toml").read_text())
    assert config["server"]["maxUploadSize"] <= 5
    assert config["theme"]["primaryColor"]


def test_page_ends_with_disclaimer_footer():
    at = run_app()
    footer = at.caption[-1].value.lower()
    assert "hackathon pilot" in footer and "not financial advice" in footer


def test_sample_documents_produce_a_report_without_errors(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    at = run_app()
    next(b for b in at.button if b.label == "Use sample documents").click().run()
    assert not at.exception
    assert not at.error
    assert "report" in at.session_state and "profile" in at.session_state
    assert any("documents read" in h.value for h in at.subheader)
    assert {
        "Financial Health Score",
        "Financial Overview",
        "AI Recommendations",
        "Spending breakdown",
        "Debt repayment plan",
    }.issubset({heading.value for heading in at.subheader})


def test_sample_report_shows_a_conversation_input_and_clear_control(monkeypatch, sample_profile):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    at = AppTest.from_file("../app.py", default_timeout=120).run()
    at.session_state["profile"] = sample_profile
    at.session_state["report"] = Report.model_validate_json(
        (Path(__file__).resolve().parents[1] / "samples" / "mock_report.json").read_text(encoding="utf-8")
    )
    at.session_state["demo"] = True
    at.run()

    assert len(at.chat_input) == 1
    assert any(button.label == "Clear chat" for button in at.button)


def test_chat_remembers_merchant_context_for_follow_up(monkeypatch, sample_profile):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(rag, "get_chat_model", lambda: None)
    at = AppTest.from_file("../app.py", default_timeout=120).run()
    at.session_state["profile"] = sample_profile
    at.session_state["report"] = Report.model_validate_json(
        (Path(__file__).resolve().parents[1] / "samples" / "mock_report.json").read_text(encoding="utf-8")
    )
    at.session_state["demo"] = True
    at.run()

    at.chat_input[0].set_value("How much did I spend on Deliveroo?").run()
    at.chat_input[0].set_value("And Tesco?").run()
    at.chat_input[0].set_value("Which one is higher?").run()
    at.chat_input[0].set_value("Why?").run()
    at.chat_input[0].set_value("What about last month?").run()

    assert [message["role"] for message in at.session_state["chat_messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert "€287.31" in at.session_state["chat_messages"][1]["content"]
    assert "€487.73" in at.session_state["chat_messages"][3]["content"]
    assert "€200.42" in at.session_state["chat_messages"][5]["content"]
    assert "€69.68" in at.session_state["chat_messages"][7]["content"]
    assert "€41.04" in at.session_state["chat_messages"][7]["content"]
    assert "€121.01" in at.session_state["chat_messages"][9]["content"]
    assert "€91.53" in at.session_state["chat_messages"][9]["content"]
    assert "across 1 transaction." in at.session_state["chat_messages"][9]["content"]

    at.chat_input[0].set_value("Could I save €100?").run()
    at.chat_input[0].set_value("I don't want to reduce takeaway.").run()
    at.chat_input[0].set_value("What else can I do?").run()
    at.chat_input[0].set_value("Thanks").run()

    assert "€107.56" in at.session_state["chat_messages"][11]["content"]
    assert "won't use takeaway reductions" in at.session_state["chat_messages"][13]["content"]
    assert "€214.40" in at.session_state["chat_messages"][15]["content"]
    assert "You're welcome" in at.session_state["chat_messages"][17]["content"]
    assert "avoid_takeaway_reduction" in at.session_state["chat_context"]["preferences"]


def test_chat_remembers_takeaway_preference_in_informal_word_order(
    monkeypatch, sample_profile
):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(rag, "get_chat_model", lambda: None)
    at = AppTest.from_file("../app.py", default_timeout=120).run()
    at.session_state["profile"] = sample_profile
    at.session_state["report"] = Report.model_validate_json(
        (Path(__file__).resolve().parents[1] / "samples" / "mock_report.json").read_text(encoding="utf-8")
    )
    at.session_state["demo"] = True
    at.run()

    at.chat_input[0].set_value("I love takeaway. I don't want to stop.").run()
    at.chat_input[0].set_value("What else can I do?").run()

    assert "avoid_takeaway_reduction" in at.session_state["chat_context"]["preferences"]
    alternative = at.session_state["chat_messages"][-1]["content"]
    assert "won't use takeaway reductions" in alternative
    assert "€214.40" in alternative
    assert "€67.97" in alternative


def test_chat_greeting_gets_a_friendly_reply_without_model(monkeypatch, sample_profile):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(rag, "get_chat_model", lambda: None)
    at = AppTest.from_file("../app.py", default_timeout=120).run()
    at.session_state["profile"] = sample_profile
    at.session_state["report"] = Report.model_validate_json(
        (Path(__file__).resolve().parents[1] / "samples" / "mock_report.json").read_text(encoding="utf-8")
    )
    at.session_state["demo"] = True
    at.run()

    at.chat_input[0].set_value("Hi").run()

    assert "Hello" in at.session_state["chat_messages"][-1]["content"]


def test_open_ended_chat_question_passes_conversation_history_without_ui_error(monkeypatch, sample_profile):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    at = AppTest.from_file("../app.py", default_timeout=120).run()
    at.session_state["profile"] = sample_profile
    at.session_state["report"] = Report.model_validate_json(
        (Path(__file__).resolve().parents[1] / "samples" / "mock_report.json").read_text(encoding="utf-8")
    )
    at.session_state["demo"] = True
    at.run()

    at.chat_input[0].set_value("Where did I spend the most money?").run()

    assert not at.exception
    assert not at.error
    assert at.session_state["chat_messages"][-1]["content"] == (
        "By category, your highest average monthly spending is housing at €1,350.00/month."
    )


def test_new_chat_and_profile_change_clear_conversation(monkeypatch, sample_profile):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(rag, "get_chat_model", lambda: None)
    at = AppTest.from_file("../app.py", default_timeout=60).run()
    at.session_state["profile"] = sample_profile
    at.session_state["report"] = Report.model_validate_json(
        (Path(__file__).resolve().parents[1] / "samples" / "mock_report.json").read_text(encoding="utf-8")
    )
    at.session_state["demo"] = True
    at.run()

    at.chat_input[0].set_value("Hi").run()
    assert at.session_state["chat_messages"]
    next(button for button in at.button if button.label == "Clear chat").click().run()
    assert at.session_state["chat_messages"] == []

    at.chat_input[0].set_value("Hi").run()
    changed_profile = sample_profile.model_copy(update={"transactions": sample_profile.transactions[1:]})
    at.session_state["profile"] = changed_profile
    at.run()
    assert at.session_state["chat_messages"] == []
