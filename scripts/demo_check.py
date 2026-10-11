"""Task D2: automated dry run of the demo script (docs/specs/00-overview.md#demo-script-acceptance-test-for-the-whole-app).

Drives the real Streamlit page headless (AppTest): uploads the sample files, reads the report and asks the
takeaway question, exactly as in the demo. Runs once without OPENROUTER_API_KEY and, if a key is set, once with it.
Every figure is checked against samples/expected.json.

    python scripts/demo_check.py                # both modes (the key comes from .env or the environment)
    python scripts/demo_check.py --offline      # only without a key
    python scripts/demo_check.py --warm-chroma  # also download Chroma's ~80 MB embedding model

Exit code 0 only when nothing failed and nothing is still unbuilt. Runbook: docs/demo-runbook.md
"""

import argparse
import json
import logging
import os
import platform
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PYMUPDF_SUGGEST_LAYOUT_ANALYZER", "0")  # hides an install hint pymupdf prints

from wealthwise import llm  # noqa: E402  (loads .env into the environment)
from wealthwise.contracts import AgentName, Report  # noqa: E402

SAMPLES = ROOT / "samples"
APP = ROOT / "app.py"
BANK_PDF = "bank_statement_jul-sep_2026.pdf"
BANK_CSV = "bank_statement_jul-sep_2026.csv"
PAYSLIP_PDF = "payslip_sep_2026.pdf"
LOAN_XLSX = "loan_statement_sep_2026.xlsx"
MIME = {".pdf": "application/pdf", ".csv": "text/csv", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
QUESTION = "How much do I spend on takeaway?"
TAKEAWAY_ANSWER = "215"  # demo script: "an answer citing about €215/month"
NO_KEY_ANSWER = "Add an OpenRouter key"  # C3 spec: the reply without a key
SLOW_SECONDS = 20  # the pitch promises results "within seconds"

PASS, FAIL, WARN, TODO, SKIP = "PASS", "FAIL", "WARN", "NOT BUILT", "SKIP"


@dataclass
class Check:
    section: str
    name: str
    status: str
    detail: str = ""


@dataclass
class DryRun:
    checks: list[Check] = field(default_factory=list)
    section: str = ""

    def record(self, name: str, status: str, detail: str = "") -> None:
        self.checks.append(Check(self.section, name, status, detail))
        mark = {PASS: "ok ", FAIL: "XX ", WARN: "!! ", TODO: "-- ", SKIP: ".. "}[status]
        print(f"  {mark}{status:<9} {name}" + (f"  ({detail})" if detail else ""), flush=True)

    def expect(self, name: str, ok: bool, detail: str = "", *, failure: str = FAIL) -> bool:
        self.record(name, PASS if ok else failure, detail)
        return ok

    def start(self, section: str) -> None:
        self.section = section
        print(f"\n{section}", flush=True)

    def guarded(self, name: str, fn: Callable, *args):
        """Run fn; a stub (NotImplementedError) is NOT BUILT, any other exception is a FAIL. Returns None on either."""
        try:
            return fn(*args)
        except NotImplementedError as e:
            self.record(name, TODO, str(e))
        except Exception as e:  # the demo must never show a traceback, so every crash is a finding
            self.record(name, FAIL, f"{type(e).__name__}: {e}")
        return None


def close(a: float | None, b: float | None) -> bool:
    return a is not None and b is not None and abs(a - b) <= 0.01


def upload(name: str) -> tuple[str, bytes, str]:
    return name, (SAMPLES / name).read_bytes(), MIME[Path(name).suffix]


def page_text(at) -> str:
    """Everything the page shows as text, so checks read what the audience would see."""
    parts = []
    for kind in ("title", "header", "subheader", "markdown", "caption", "text", "info", "success", "warning", "error", "metric", "code", "json"):
        for el in getattr(at, kind):
            parts += [str(getattr(el, attr, "") or "") for attr in ("label", "value", "body")]
    for kind in ("table", "dataframe"):
        for el in getattr(at, kind):
            parts.append(str(el.value))
    return "\n".join(parts)


def report_numbers(report: Report) -> dict:
    """The report without LLM-written words: what must be identical across bank formats and with or without a key."""
    data = report.model_dump(mode="json", exclude={"llm_used"})
    for rec in data["recommendations"]:
        rec.pop("title")
        rec.pop("detail")
    return data


# ---------- Preflight ----------


def preflight(run: DryRun, key: str | None) -> None:
    run.start("Preflight (docs/COLLABORATION.md step 1)")
    run.expect("Python 3.11 or newer", sys.version_info >= (3, 11), platform.python_version())
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        if "==" not in line or line.lstrip().startswith("#"):
            continue
        name, pinned = (s.strip() for s in line.split("==", 1))
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            run.record(f"{name} installed", FAIL, f"missing: pip install -r requirements.txt")
            continue
        run.expect(f"{name}=={pinned}", installed == pinned, "" if installed == pinned else f"installed {installed}", failure=WARN)
    missing = [n for n in (BANK_PDF, BANK_CSV, PAYSLIP_PDF, LOAN_XLSX, "expected.json") if not (SAMPLES / n).exists()]
    run.expect("sample documents present", not missing, ", ".join(missing))
    run.record("OPENROUTER_API_KEY", PASS if key else SKIP, "set" if key else "not set: only the offline run happens")


def warm_chroma(run: DryRun) -> None:
    run.start("Warm up Chroma (first run downloads ~80 MB)")
    try:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        started = time.perf_counter()
        DefaultEmbeddingFunction()(["warm-up"])
        run.record("embedding model ready", PASS, f"{time.perf_counter() - started:.1f}s")
    except Exception as e:
        run.record("embedding model ready", FAIL, f"{type(e).__name__}: {e}. Needs internet once")


# ---------- The demo script, through the UI ----------


def demo_in_app(run: DryRun, bank_file: str, expected: dict, with_key: bool):
    """Demo steps 1-5 through the real page. Returns the Report the page built, or None."""
    from streamlit.testing.v1 import AppTest

    # AppTest runs the page "bare"; Streamlit then warns once per run that there's no ScriptRunContext.
    logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)
    files = [bank_file, PAYSLIP_PDF, LOAN_XLSX]
    at = AppTest.from_file(str(APP), default_timeout=180).run()
    if not run.expect("page loads", not at.exception, str(at.exception[0].value) if at.exception else ""):
        return None
    at.file_uploader[0].set_value([upload(n) for n in files]).run()
    started = time.perf_counter()
    next(b for b in at.button if b.label == "Analyse").click().run()
    seconds = time.perf_counter() - started

    # Step 1-2: "3 documents read" with no errors
    if at.exception:
        run.record("analyse without a traceback", FAIL, str(at.exception[0].value)[:200])
        return None
    run.expect("no error messages", not at.error, "; ".join(e.value for e in at.error)[:200])
    run.expect("analysis time", seconds < SLOW_SECONDS, f"{seconds:.1f}s", failure=WARN)
    state = at.session_state
    if not run.expect("report built", "report" in state):
        return None
    run.expect("real data, not the demo fallback", not state["demo"],
               "" if not state["demo"] else "a stage still raises NotImplementedError, so the page shows samples/mock_report.json")
    run.expect("'3 documents read'", any(h.value == "3 documents read" for h in at.subheader),
               "; ".join(h.value for h in at.subheader))
    run.expect("no document warnings", not at.warning, "; ".join(w.value for w in at.warning)[:200])

    # Step 3-4: the figures, computed correctly...
    report: Report = state["report"]
    hs, dp = report.health_score, report.debt_plan
    run.expect(f"Health Score {expected['health_score']['score']} ({expected['health_score']['band']}) with 4 components",
               (hs.score, hs.band, len(hs.components)) == (expected["health_score"]["score"], expected["health_score"]["band"], 4),
               f"got {hs.score} ({hs.band}), {len(hs.components)} components")
    run.expect(f"cuts EUR {expected['identified_cuts']}/month", close(report.identified_cuts, expected["identified_cuts"]), f"got {report.identified_cuts}")
    run.expect(f"debt-free {expected['debt_plan']['months_saved']} months earlier",
               dp is not None and dp.months_saved == expected["debt_plan"]["months_saved"], f"got {dp and dp.months_saved}")
    run.expect(f"saves EUR {expected['debt_plan']['interest_saved']} interest",
               dp is not None and close(dp.interest_saved, expected["debt_plan"]["interest_saved"]), f"got {dp and dp.interest_saved}")
    agents = [r.agent for r in report.recommendations]
    run.expect("3 recommendations: spending, debt, savings", agents == [AgentName.SPENDING, AgentName.DEBT, AgentName.SAVINGS],
               ", ".join(a.value for a in agents))
    impacts = [r.monthly_impact for r in report.recommendations]
    wanted = [expected["identified_cuts"], expected["debt_plan"]["extra_monthly_payment"], expected["savings_plan"]["monthly_amount"]]
    run.expect("recommendation impacts come from code", len(impacts) == 3 and all(close(a, b) for a, b in zip(impacts, wanted)), f"got {impacts}")
    if with_key:
        run.expect("LLM wrote the wording (llm_used)", report.llm_used, "" if report.llm_used else "calls failed, template text shown", failure=WARN)
        quoted = [f"{r.monthly_impact:.2f}" in (r.title + r.detail).replace(",", "") for r in report.recommendations]
        run.expect("LLM text quotes the computed figures", all(quoted), f"quoted: {quoted}", failure=WARN)
    else:
        run.expect("template text without a key (llm_used False)", not report.llm_used)

    # ...and shown on the page (C2)
    text = page_text(at)
    shown = {"Health Score": str(hs.score), "cuts": f"{report.identified_cuts:.2f}", "interest saved": f"{dp.interest_saved:.2f}" if dp else "n/a"}
    missing = [label for label, value in shown.items() if value not in text.replace(",", "")]
    if missing:
        from wealthwise import dashboard

        built = run.guarded("report view (C2)", dashboard.format_eur, 0.0) is not None
        if built:
            run.record("page shows score, cuts and interest saved", FAIL, f"not on the page: {', '.join(missing)}")
    else:
        run.record("page shows score, cuts and interest saved", PASS)

    # Step 5: Ask WealthWise
    at.text_input[0].input(QUESTION).run()
    if at.exception:
        run.record("Ask WealthWise", FAIL, str(at.exception[0].value)[:200])
    elif any("coming soon" in i.value for i in at.info):
        run.record("Ask WealthWise (C3)", TODO, "page says 'coming soon'")
    else:
        answer = page_text(at).split("Ask a question about your finances")[-1].strip()
        if with_key:
            run.expect(f"'{QUESTION}' cites about EUR {TAKEAWAY_ANSWER}/month", TAKEAWAY_ANSWER in answer, answer[:160])
        else:
            run.expect("Ask without a key explains how to enable it", NO_KEY_ANSWER in answer, answer[:160])
    return report


def demo_mode(run: DryRun, expected: dict, key: str | None, with_key: bool) -> Report | None:
    if with_key:
        os.environ["OPENROUTER_API_KEY"] = key
    else:
        os.environ.pop("OPENROUTER_API_KEY", None)
    label = "with OPENROUTER_API_KEY" if with_key else "without OPENROUTER_API_KEY (offline fallback)"

    run.start(f"Demo steps 1-5, PDF bank statement, {label}")
    from_pdf = run.guarded("demo with the PDF", demo_in_app, run, BANK_PDF, expected, with_key)

    run.start(f"Demo step 6, CSV bank statement instead, {label}")
    from_csv = run.guarded("demo with the CSV", demo_in_app, run, BANK_CSV, expected, with_key)
    if from_pdf and from_csv:
        run.expect("CSV gives identical numbers to the PDF", report_numbers(from_pdf) == report_numbers(from_csv))
    return from_pdf


# ---------- Report ----------


def summary(run: DryRun) -> int:
    counts = {s: sum(c.status == s for c in run.checks) for s in (PASS, FAIL, WARN, TODO, SKIP)}
    print("\nSummary: " + ", ".join(f"{n} {s.lower()}" for s, n in counts.items() if n))
    todo = [c for c in run.checks if c.status == TODO]
    if todo:
        print("\nStill unbuilt (already have issues; see docs/specs/00-overview.md):")
        for c in dict.fromkeys(f"{c.name}: {c.detail}" for c in todo):
            print(f"  - {c}")
    problems = [c for c in run.checks if c.status in (FAIL, WARN)]
    if problems:
        print("\nFile each problem as a needs-triage issue (docs/COLLABORATION.md, 'When something goes wrong'):")
        for c in problems:
            body = f"Found by scripts/demo_check.py ({c.section}). {c.status}: {c.name}. {c.detail}".replace('"', "'")
            print(f'  gh issue create --label needs-triage --title "Demo: {c.name}" --body "{body}"')
    ready = not (counts[FAIL] or counts[TODO])
    print("\nDemo ready." if ready else "\nDemo NOT ready.")
    return 0 if ready else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--offline", action="store_true", help="only run without OPENROUTER_API_KEY")
    parser.add_argument("--warm-chroma", action="store_true", help="download Chroma's embedding model now")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    os.chdir(ROOT)

    commit = subprocess.run(["git", "log", "-1", "--format=%h %s"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    print(f"WealthWise demo dry run, {time.strftime('%Y-%m-%d %H:%M')}, at {commit or 'unknown commit'}")

    key = os.environ.get("OPENROUTER_API_KEY") or None
    expected = json.loads((SAMPLES / "expected.json").read_text(encoding="utf-8"))
    run = DryRun()
    preflight(run, key)
    if args.warm_chroma:
        warm_chroma(run)

    offline = demo_mode(run, expected, key, with_key=False)
    if key and not args.offline:
        online = demo_mode(run, expected, key, with_key=True)
        if offline and online:
            run.start("Numbers don't depend on the LLM (ADR-0001)")
            run.expect("same numbers with and without a key", report_numbers(offline) == report_numbers(online))
    if key:
        os.environ["OPENROUTER_API_KEY"] = key
    return summary(run)


if __name__ == "__main__":
    sys.exit(main())
