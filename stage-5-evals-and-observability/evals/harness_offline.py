"""CLI entry point for the offline eval harness.

Run with:  python -m evals.harness_offline
"""

from orchestrator.code_driven import CodeDrivenOrchestrator
from evals.harness import EvalHarness


def main() -> None:
    print("=" * 60)
    print("STAGE 5 — OFFLINE EVAL HARNESS")
    print("=" * 60)
    orchestrator = CodeDrivenOrchestrator()
    harness = EvalHarness(orchestrator, user_id="user:eval")
    harness.run_offline()
    print("\nDone. Inspect eval_results and runs.metadata in Postgres.")


if __name__ == "__main__":
    main()
