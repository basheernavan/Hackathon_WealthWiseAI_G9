"""Run the Ask WealthWise eval set (wealthwise/evals.py) as a LangSmith experiment.

Needs OPENROUTER_API_KEY and LANGSMITH_API_KEY in .env. Usage: python scripts/run_evals.py
"""

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402
from langsmith import Client, evaluate  # noqa: E402

from wealthwise import evals  # noqa: E402


def main() -> None:
    load_dotenv(ROOT / ".env")
    missing = [key for key in ("OPENROUTER_API_KEY", "LANGSMITH_API_KEY") if not os.getenv(key)]
    if missing:
        sys.exit(f"Add {', '.join(missing)} to .env first.")
    os.environ.setdefault("LANGSMITH_TRACING", "true")

    # The name changes with the cases, so editing CASES creates a fresh dataset instead of reusing a stale one.
    digest = hashlib.sha256(json.dumps(evals.CASES, sort_keys=True).encode()).hexdigest()[:8]
    dataset_name = f"wealthwise-ask-{digest}"
    client = Client()
    if not client.has_dataset(dataset_name=dataset_name):
        dataset = client.create_dataset(dataset_name, description="Ask WealthWise questions on the sample documents.")
        client.create_examples(
            dataset_id=dataset.id,
            examples=[
                {"inputs": {"question": case["question"]}, "outputs": evals.reference_outputs(case)}
                for case in evals.CASES
            ],
        )

    profile, report = evals.load_sample()
    results = evaluate(
        evals.target(profile, report),
        data=dataset_name,
        evaluators=[evals.outcome_matches, evals.figure_present],
        experiment_prefix="ask-wealthwise",
        max_concurrency=2,
        client=client,
    )
    failures = 0
    for row in results:
        scores = {result.key: result.score for result in row["evaluation_results"]["results"]}
        passed = all(scores.values())
        failures += not passed
        print(f"{'PASS' if passed else 'FAIL'}  {row['example'].inputs['question']}  {scores}")
    print(f"\n{len(evals.CASES) - failures}/{len(evals.CASES)} passed. Experiment: {results.experiment_name}")


if __name__ == "__main__":
    main()
