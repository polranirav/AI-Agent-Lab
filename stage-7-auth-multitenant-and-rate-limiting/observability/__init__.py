"""
Observability layer for Stage 5.

Always-on instrumentation around live traffic and the eval harness:
  - metrics : per-run latency, token usage, and cost (persisted to runs.metadata)
  - tracing : a run_timer context manager that times a run and records metrics

Everything is keyed by run_id, so observability data sits on the same trace as
runs, events, guardrail_events, and eval_results.
"""

from observability import metrics, tracing

__all__ = ["metrics", "tracing"]
