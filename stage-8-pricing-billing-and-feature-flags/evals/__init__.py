"""
Evaluation harness for Stage 5.

Turns the system into a measurable one. Modules:
  - store    : save_eval_result -> writes scores into the eval_results table
  - metrics  : rule-based metrics (e.g. task completion)
  - judge    : LLM-as-a-judge quality scoring (relevance, brand/tone)
  - datasets : curated offline eval prompts
  - harness  : EvalHarness that runs the orchestrator and scores each run

Every score lands in eval_results keyed by run_id, alongside the run's
observability metrics and guardrail events.
"""

from evals import store, metrics, judge, datasets, harness

__all__ = ["store", "metrics", "judge", "datasets", "harness"]
