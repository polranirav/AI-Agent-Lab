"""Rule-based (deterministic) evaluation metrics."""

from typing import Any, Dict, Optional

from evals.store import save_eval_result


def metric_task_completion(run_id: str, session_id: Optional[str],
                           result: Dict[str, Any]) -> float:
    """Check whether the orchestrator returned all required artifacts.

    Target shape for the Creator Orchestrator: 5 clips, 2 posts, 1 email.
    Score: 1.0 if all present, partial if some missing, 0.0 if none.
    """
    clips = result.get("clips") or []
    posts = result.get("posts") or []
    email = result.get("email")

    score = 1.0
    reasons = []

    if len(clips) < 5:
        score -= 0.5
        reasons.append(f"Expected >=5 clips, got {len(clips)}")
    if len(posts) < 2:
        score -= 0.25
        reasons.append(f"Expected >=2 posts, got {len(posts)}")
    if not email:
        score -= 0.25
        reasons.append("Missing email copy")

    if score < 0:
        score = 0.0

    save_eval_result(
        run_id=run_id,
        session_id=session_id,
        evaluator="task_completion",
        scope="run",
        target="orchestrator",
        score=score,
        label="pass" if score >= 0.75 else "fail",
        details={"reasons": reasons},
    )
    return score
