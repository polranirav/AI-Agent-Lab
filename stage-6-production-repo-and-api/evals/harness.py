"""The evaluation harness: replay the orchestrator over a dataset and score it.

Two modes:
  - run_offline()          : run curated prompts through the orchestrator (CI/local)
  - run_on_existing_runs() : re-score already-recorded production runs (online)

The harness uses the SAME orchestrator and agents as production, reuses tracing
and run logging, and writes every score to eval_results.
"""

from typing import List

from memory import short_term, episodic
from observability.tracing import run_timer
from evals.metrics import metric_task_completion
from evals.judge import judge_brand_fit
from evals.datasets import offline_eval_dataset


class EvalHarness:
    def __init__(self, orchestrator, user_id: str = "user:eval"):
        self.orchestrator = orchestrator
        self.user_id = user_id

    def run_offline(self) -> None:
        """Run the offline eval dataset through the orchestrator and score each run."""
        for case in offline_eval_dataset():
            topic = case["topic"]
            brief = case["brief"]

            session_id = short_term.create_session(user_id=self.user_id, topic=topic)
            run_id = episodic.start_run(
                session_id, orchestrator="eval-offline", metadata={"topic": topic},
            )

            with run_timer(run_id, session_id):
                # orchestrator.run returns a structured dict with all artifacts.
                result = self.orchestrator.run(
                    topic=topic, user_id=self.user_id,
                    session_id=session_id, run_id=run_id, brief=brief,
                )

            episodic.finish_run(run_id, status="success")

            # 1) Rule-based completion metric (run-level).
            completion = metric_task_completion(run_id, session_id, result)

            # 2) LLM-as-judge brand fit for each generated post (agent-level).
            posts = result.get("posts") or []
            judge_scores = []
            for idx, post in enumerate(posts):
                score = judge_brand_fit(
                    run_id, session_id, brief=brief,
                    content=post, target=f"post[{idx}]",
                )
                judge_scores.append(score)

            avg_judge = sum(judge_scores) / len(judge_scores) if judge_scores else 0.0
            print(f"Evaluated run {run_id}")
            print(f"  topic           : {topic}")
            print(f"  task_completion : {completion}")
            print(f"  brand_fit (avg) : {avg_judge:.2f} over {len(posts)} post(s)")

    def run_on_existing_runs(self, run_ids: List[str]) -> None:
        """Re-score existing production runs (requires stored structured outputs)."""
        # Future: load saved structured results for each run_id and re-score them.
        raise NotImplementedError("Online replay eval not implemented yet.")
