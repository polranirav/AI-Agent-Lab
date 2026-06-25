"""Tracing helpers: time a full run and flush its metrics.

Usage:
    run_id = episodic.start_run(...)
    with run_timer(run_id, session_id) as rmetrics:
        result = orchestrator.run(...)
    episodic.finish_run(run_id, status="success")
"""

import time
from contextlib import contextmanager
from typing import Generator, Optional

from observability.metrics import (
    RunMetrics,
    estimate_cost,
    pop_token_usage,
    record_run_metrics,
)


@contextmanager
def run_timer(run_id: str,
              session_id: Optional[str] = None,
              model: str = "gpt-4o-mini") -> Generator[RunMetrics, None, None]:
    """Context manager that times a run and persists latency/tokens/cost."""
    metrics = RunMetrics()
    start = time.perf_counter()
    try:
        yield metrics
    finally:
        metrics.latency_ms = (time.perf_counter() - start) * 1000

        # Pull whatever token usage agents accumulated for this run.
        prompt, completion = pop_token_usage(run_id)
        metrics.token_prompt = prompt
        metrics.token_completion = completion
        metrics.token_total = prompt + completion
        metrics.cost_usd = estimate_cost(prompt, completion, model)

        record_run_metrics(run_id, session_id, metrics)
