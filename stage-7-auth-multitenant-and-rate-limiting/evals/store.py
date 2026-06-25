"""Eval store: the single write helper everything else builds on."""

from typing import Any, Optional

from memory.db import get_cursor, as_jsonb


def save_eval_result(run_id: str,
                     session_id: Optional[str],
                     evaluator: str,
                     scope: str,
                     target: str,
                     score: float,
                     label: Optional[str] = None,
                     details: Optional[dict[str, Any]] = None) -> None:
    """Insert one evaluation result into eval_results."""
    details = details or {}
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO eval_results
                (run_id, session_id, evaluator, scope, target, score, label, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (run_id, session_id, evaluator, scope, target,
             score, label, as_jsonb(details)),
        )
