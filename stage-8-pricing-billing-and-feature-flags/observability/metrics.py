"""Run-level metrics: latency, token usage, and cost.

Token usage is accumulated in-process per run_id (LLM calls report their usage
via `add_token_usage`), then flushed into the metrics when the run finishes.
The final numbers are persisted onto the existing `runs.metadata` JSONB column,
so no new table is needed for observability.
"""

import json
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from memory.db import get_cursor

# Approximate USD price per 1M tokens. Used for a rough per-run cost estimate.
# (Chat models dominate cost here; embeddings are billed separately and small.)
PRICES_PER_1M = {
    "gpt-4o":      {"prompt": 2.50, "completion": 10.00},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
}
_DEFAULT_MODEL = "gpt-4o-mini"


@dataclass
class RunMetrics:
    latency_ms: float = 0.0
    token_prompt: int = 0
    token_completion: int = 0
    token_total: int = 0
    cost_usd: float = 0.0


# ── In-process token accumulator (keyed by run_id) ───────────────────
_RUN_TOKENS: Dict[str, Dict[str, int]] = {}


def add_token_usage(run_id: Optional[str], prompt: int, completion: int) -> None:
    """Called after each LLM response to accumulate token usage for a run."""
    if not run_id:
        return
    bucket = _RUN_TOKENS.setdefault(run_id, {"prompt": 0, "completion": 0})
    bucket["prompt"] += int(prompt or 0)
    bucket["completion"] += int(completion or 0)


def pop_token_usage(run_id: str) -> Tuple[int, int]:
    """Return and clear accumulated (prompt, completion) tokens for a run."""
    bucket = _RUN_TOKENS.pop(run_id, {"prompt": 0, "completion": 0})
    return bucket["prompt"], bucket["completion"]


def estimate_cost(prompt: int, completion: int, model: str = _DEFAULT_MODEL) -> float:
    """Rough USD cost for the given token counts at the model's price."""
    rates = PRICES_PER_1M.get(model, PRICES_PER_1M[_DEFAULT_MODEL])
    return (prompt / 1_000_000) * rates["prompt"] + \
           (completion / 1_000_000) * rates["completion"]


def record_run_metrics(run_id: str, session_id: Optional[str],
                       metrics: RunMetrics) -> None:
    """Persist run-level metrics by enriching the runs.metadata JSONB column."""
    payload = {
        "latency_ms": round(metrics.latency_ms, 2),
        "token_prompt": metrics.token_prompt,
        "token_completion": metrics.token_completion,
        "token_total": metrics.token_total,
        "cost_usd": round(metrics.cost_usd, 6),
    }
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE runs
            SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
            WHERE id = %s
            """,
            (json.dumps(payload), run_id),
        )
