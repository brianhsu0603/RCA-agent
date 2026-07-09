"""Minimal offline eval harness for the RCA agent.

Runs each labeled scenario in eval_set.json through the real agent (real tool
calls against the seeded DB, real model calls) and checks whether any of the
expected keywords for the true root cause show up in the top-3 hypotheses.
This is a starting point for accuracy tracking, not a substitute for RCA-engineer
review - extend it with human-graded scores as real incident outcomes accumulate.

Run with: python -m app.eval.run_eval
"""

import json
from pathlib import Path

from app.agents.rca_agent import run_rca
from app.db import SessionLocal
from app.ingestion.seed import seed

EVAL_SET_PATH = Path(__file__).resolve().parent / "eval_set.json"


def scenario_hit(hypotheses, expected_keywords: list[str], top_n: int = 3) -> bool:
    top = sorted(hypotheses, key=lambda h: h.confidence, reverse=True)[:top_n]
    text = " ".join(f"{h.description} {h.reasoning}" for h in top).lower()
    return any(kw.lower() in text for kw in expected_keywords)


def main() -> None:
    seed()
    scenarios = json.loads(EVAL_SET_PATH.read_text())

    db = SessionLocal()
    results = []
    try:
        for s in scenarios:
            report = run_rca(db, s["symptom"], s["station"], s["test_id"])
            hit = scenario_hit(report.hypotheses, s["expected_keywords"])
            results.append((s["name"], hit, report))
    finally:
        db.close()

    print("\n=== RCA Eval Report ===")
    for name, hit, report in results:
        status = "PASS" if hit else "FAIL"
        top = sorted(report.hypotheses, key=lambda h: h.confidence, reverse=True)[0]
        print(f"[{status}] {name}")
        print(f"       top hypothesis ({top.confidence:.2f}): {top.description}")

    passed = sum(1 for _, hit, _ in results if hit)
    print(f"\n{passed}/{len(results)} scenarios had the expected root cause in the top 3 hypotheses.")


if __name__ == "__main__":
    main()
