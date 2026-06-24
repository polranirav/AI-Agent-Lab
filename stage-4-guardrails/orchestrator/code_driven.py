from typing import Optional
from openai import OpenAI
from config import OPENAI_API_KEY, AGENT_MODEL
from agents.research_agent  import ResearchAgent
from agents.writer_agent    import WriterAgent
from agents.reviewer_agent  import ReviewerAgent
from orchestrator.schemas   import ResearchOutput, WritingOutput, ReviewOutput
from memory import short_term, episodic


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
        return response.choices[0].message.parsed

    def run(self, topic: str, user_id: Optional[str] = None) -> dict:
        """
        Run the full blog post pipeline for a given topic.
        Returns a dict with research, draft, and review.
        """
        print(f"\n{'='*60}")
        print(f"CODE-DRIVEN ORCHESTRATOR: '{topic}'")
        print(f"{'='*60}")

        # Memory: open a session (short-term) and a run (episodic).
        session_id = short_term.create_session(user_id=user_id, topic=topic)
        run_id = episodic.start_run(
            session_id, orchestrator="code-driven", metadata={"topic": topic},
        )

        try:
            return self._run(topic, session_id, run_id, user_id)
        except Exception as e:
            episodic.finish_run(run_id, status="error", error=str(e))
            raise

    def _run(self, topic: str, session_id: str, run_id: str,
             user_id: Optional[str] = None) -> dict:
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

        result = {
            "topic":        topic,
            "research":     research.model_dump(),
            "draft":        draft.model_dump(),
            "review":       review.model_dump(),
            "session_id":   session_id,
            "run_id":       run_id,
            "pipeline":     "code-driven",
        }
        episodic.finish_run(run_id, status="success")
        return result