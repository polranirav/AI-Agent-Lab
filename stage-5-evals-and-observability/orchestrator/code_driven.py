from typing import Optional
from openai import OpenAI
from config import OPENAI_API_KEY, AGENT_MODEL
from agents.research_agent  import ResearchAgent
from agents.writer_agent    import WriterAgent
from agents.reviewer_agent  import ReviewerAgent
from orchestrator.schemas   import ResearchOutput, WritingOutput, ReviewOutput
from memory import short_term, episodic
from observability.tracing import run_timer
from observability.metrics import add_token_usage


class CodeDrivenOrchestrator:
    """
    Deterministic pipeline orchestrator.
    Flow: research → write → review → synthesize.
    The orchestrator controls exactly which agent runs and when.
    """

    def __init__(self):
        self.research_agent  = ResearchAgent()
        self.writer_agent    = WriterAgent()
        self.reviewer_agent  = ReviewerAgent()
        self.client          = OpenAI(api_key=OPENAI_API_KEY)
        self._active_run_id  = None  # set per run for token attribution

    def _parse_structured(self, agent, user_msg: str, schema, context: str = ""):
        """
        Run an agent and parse its output into a structured Pydantic model.
        Uses OpenAI structured outputs for guaranteed JSON.
        """
        system = agent.system_prompt
        if context:
            system += f"\n\n--- CONTEXT ---\n{context}"

        system += (
            "\n\nIMPORTANT: You MUST respond with valid JSON only, "
            "matching the exact schema provided. No other text."
        )

        response = self.client.beta.chat.completions.parse(
            model=AGENT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_msg},
            ],
            response_format=schema,
        )
        # Observability: aggregate token usage for this run (the active run is
        # set on the instance during _run) into the run's metrics.
        if response.usage and self._active_run_id:
            add_token_usage(self._active_run_id,
                            response.usage.prompt_tokens,
                            response.usage.completion_tokens)
        return response.choices[0].message.parsed

    def run(self, topic: str, user_id: Optional[str] = None,
            session_id: Optional[str] = None,
            run_id: Optional[str] = None,
            brief: Optional[str] = None) -> dict:
        """
        Run the full blog post pipeline for a given topic and return a
        structured result dict (topic, brief, research, draft, review, posts,
        email, clips).

        Stage 5: session_id/run_id may be created upstream (by the eval harness)
        and passed in. When they are NOT provided, the orchestrator owns the run
        — it opens a session/run, times the run, and finishes it. When they ARE
        provided, the caller owns timing and finishing.
        """
        print(f"\n{'='*60}")
        print(f"CODE-DRIVEN ORCHESTRATOR: '{topic}'")
        print(f"{'='*60}")

        owns_run = run_id is None
        if session_id is None:
            session_id = short_term.create_session(user_id=user_id, topic=topic)
        if run_id is None:
            run_id = episodic.start_run(
                session_id, orchestrator="code-driven", metadata={"topic": topic},
            )

        if not owns_run:
            # Caller (eval harness) owns timing + finish_run.
            return self._run(topic, session_id, run_id, user_id, brief)

        # Standalone run: time it and finish it ourselves.
        try:
            with run_timer(run_id, session_id):
                result = self._run(topic, session_id, run_id, user_id, brief)
            episodic.finish_run(run_id, status="success")
            return result
        except Exception as e:
            episodic.finish_run(run_id, status="error", error=str(e))
            raise

    def _run(self, topic: str, session_id: str, run_id: str,
             user_id: Optional[str] = None,
             brief: Optional[str] = None) -> dict:
        # Remember the active run so _parse_structured can attribute tokens.
        self._active_run_id = run_id
        # ── Step 1: Research ──────────────────────────────────────────
        print("\n[Step 1] ResearchAgent running...")
        raw_research = self.research_agent.run_and_store(
            topic, session_id=session_id, run_id=run_id, user_id=user_id,
        )

        # Parse into structured output
        research: ResearchOutput = self._parse_structured(
            self.research_agent,
            f"Research this topic and return structured output: {topic}",
            ResearchOutput
        )
        print(f"  Summary: {research.summary[:80]}...")
        print(f"  Key points: {len(research.key_points)} found")

        # ── Step 2: Write ─────────────────────────────────────────────
        print("\n[Step 2] WriterAgent running...")
        research_context = (
            (f"Brief: {brief}\n\n" if brief else "") +
            f"Summary: {research.summary}\n"
            f"Key Points:\n" +
            "\n".join(f"- {p}" for p in research.key_points) +
            f"\nFacts:\n" +
            "\n".join(f"- {f}" for f in research.facts)
        )

        draft: WritingOutput = self._parse_structured(
            self.writer_agent,
            f"Write a blog post about: {topic}",
            WritingOutput,
            context=research_context
        )
        print(f"  Title: {draft.title}")
        print(f"  Word count: {draft.word_count}")

        # ── Step 3: Review ────────────────────────────────────────────
        print("\n[Step 3] ReviewerAgent running...")
        draft_context = f"TITLE: {draft.title}\n\nCONTENT:\n{draft.content}"

        review: ReviewOutput = self._parse_structured(
            self.reviewer_agent,
            "Review this blog post draft:",
            ReviewOutput,
            context=draft_context
        )
        print(f"  Verdict: {review.verdict}")
        print(f"  Strengths: {len(review.strengths)}")
        print(f"  Improvements: {len(review.improvements)}")

        # ── Step 4: Synthesize ────────────────────────────────────────
        print("\n[Step 4] Synthesizing final output...")

        # Map this blog pipeline's artifacts onto the Creator Orchestrator shape
        # the eval harness expects (clips / posts / email). This pipeline produces
        # one post (the blog draft); clips/email belong to the fuller product, so
        # task_completion will score this as partial — which is the point.
        result = {
            "topic":        topic,
            "brief":        brief,
            "research":     research.model_dump(),
            "draft":        draft.model_dump(),
            "review":       review.model_dump(),
            "posts":        [draft.content],
            "email":        None,
            "clips":        [],
            "session_id":   session_id,
            "run_id":       run_id,
            "pipeline":     "code-driven",
        }
        return result