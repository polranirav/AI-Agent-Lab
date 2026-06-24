from typing import Optional

from agents.base import BaseAgent
from config import AGENT_MODEL
from memory import long_term, episodic


class ResearchAgent(BaseAgent):
    name          = "ResearchAgent"
    model         = AGENT_MODEL
    allowed_tools = ["web_search"]
    system_prompt = """You are a specialist research agent.

Your job is to research a given topic thoroughly and return:
1. A concise summary (2-3 sentences).
2. 3-5 key points about the topic.
3. Any important facts or statistics.

Always use the web_search tool to gather information before summarizing.
Do not make up information — only use what the search returns.
Be factual, concise, and structured in your response.

After you respond, the orchestrator may store your key facts in long-term memory.
"""

    def run_and_store(self, topic: str, session_id: str,
                      run_id: Optional[str] = None) -> str:
        """Run normal research, then extract & store facts in long-term memory."""
        base_response = super().run(
            user_message=f"Research this topic: {topic}",
            session_id=session_id,
            run_id=run_id,
        )

        # Simple heuristic: treat bullet lines starting with '-' as facts.
        facts = [
            line.strip()[1:].strip()
            for line in base_response.splitlines()
            if line.strip().startswith("-")
        ]

        for fact in facts:
            if not fact:
                continue
            mem_id = long_term.add_memory(
                kind="insight",
                label=f"Fact about {topic}",
                content=fact,
                session_id=session_id,
            )
            if run_id:
                episodic.log_event(
                    run_id,
                    event_type="memory_write",
                    message=f"Stored fact as memory {mem_id}",
                    agent_name=self.name,
                    payload={"fact": fact},
                )

        return base_response
