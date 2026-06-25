"""Thin façade for running evaluations and reading scores."""

from typing import Any, Dict, List

from evals.harness import EvalHarness
from memory.db import get_cursor
from app.orchestrator import build_orchestrator


def run_offline_evals(user_id: str = "user:eval") -> None:
    """Run the offline eval dataset through the orchestrator and score it."""
    harness = EvalHarness(build_orchestrator(), user_id=user_id)
    harness.run_offline()


def recent_scores(limit: int = 20) -> List[Dict[str, Any]]:
    """Read the most recent eval_results rows (for a dashboard/report)."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT created_at, evaluator, scope, target, score, label
            FROM eval_results
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return [
        {
            "created_at": r[0], "evaluator": r[1], "scope": r[2],
            "target": r[3], "score": r[4], "label": r[5],
        }
        for r in rows
    ]
