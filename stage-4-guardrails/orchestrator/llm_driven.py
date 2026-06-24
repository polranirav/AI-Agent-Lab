import json
from typing import Optional
from openai import OpenAI
from config import OPENAI_API_KEY, ORCHESTRATOR_MODEL
from agents.research_agent  import ResearchAgent
from agents.writer_agent    import WriterAgent
from agents.reviewer_agent  import ReviewerAgent
from memory import short_term, episodic


class LLMDrivenOrchestrator:
    """
    Dynamic orchestrator where specialist agents are tools.
    The LLM decides which agent to call, when, and in what order.
    """

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.research_agent  = ResearchAgent()
        self.writer_agent    = WriterAgent()
        self.reviewer_agent  = ReviewerAgent()
        self._context_store  = {}    # holds inter-agent results
        self._session_id     = None  # set per run() for memory wiring
        self._run_id         = None
        self._user_id        = None  # set per run() for tool RBAC

    # ── Agent wrappers as tool functions ─────────────────────────────
    def _call_research_agent(self, topic: str) -> str:
        result = self.research_agent.run_and_store(
            topic, session_id=self._session_id, run_id=self._run_id,
            user_id=self._user_id,
        )
        self._context_store["research"] = result
        return result

    def _call_writer_agent(self, topic: str) -> str:
        context = self._context_store.get("research", "")
        result  = self.writer_agent.run(
            f"Write a blog post about: {topic}",
            context=context,
            session_id=self._session_id,
            run_id=self._run_id,
            user_id=self._user_id,
        )
        self._context_store["draft"] = result
        return result

    def _call_reviewer_agent(self, draft: str = "") -> str:
        if not draft:
            draft = self._context_store.get("draft", "No draft found.")
        return self.reviewer_agent.run(
            "Review this draft:", context=draft,
            session_id=self._session_id, run_id=self._run_id,
            user_id=self._user_id,
        )

    # ── Tool schemas for the orchestrator ────────────────────────────
    AGENT_TOOL_SCHEMAS = [
        {
            "type": "function",
            "function": {
                "name": "call_research_agent",
                "description": "Calls the ResearchAgent to research a topic. Returns facts, key points, and a summary.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic to research"}
                    },
                    "required": ["topic"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "call_writer_agent",
                "description": "Calls the WriterAgent to write a blog post. Should be called AFTER research is done.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic to write about"}
                    },
                    "required": ["topic"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "call_reviewer_agent",
                "description": "Calls the ReviewerAgent to review the most recent draft. Should be called AFTER writing is done.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "draft": {
                            "type": "string",
                            "description": "Optional: pass a specific draft to review. Leave empty to review the latest draft."
                        }
                    },
                    "required": []
                }
            }
        }
    ]

    SYSTEM_PROMPT = """You are an orchestrator agent managing a blog post creation pipeline.

You have access to three specialist agents as tools:
- call_research_agent: researches a topic
- call_writer_agent: writes a blog post (requires research context)
- call_reviewer_agent: reviews the most recent draft

Your job:
1. Research the topic first.
2. Then write a blog post using the research.
3. Then review the draft.
4. Finally, return a concise summary of what was produced.

Always follow this sequence. Do not skip steps.
"""

    def run(self, topic: str, user_id: Optional[str] = None) -> dict:
        print(f"\n{'='*60}")
        print(f"LLM-DRIVEN ORCHESTRATOR: '{topic}'")
        print(f"{'='*60}")

        # Memory: open a session (short-term) and a run (episodic).
        self._user_id = user_id
        self._session_id = short_term.create_session(user_id=user_id, topic=topic)
        self._run_id = episodic.start_run(
            self._session_id, orchestrator="llm-driven", metadata={"topic": topic},
        )

        try:
            return self._run(topic)
        except Exception as e:
            episodic.finish_run(self._run_id, status="error", error=str(e))
            raise

    def _run(self, topic: str) -> dict:
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user",   "content": f"Create a blog post about: {topic}"},
        ]

        agent_dispatch = {
            "call_research_agent": self._call_research_agent,
            "call_writer_agent":   self._call_writer_agent,
            "call_reviewer_agent": self._call_reviewer_agent,
        }

        for iteration in range(10):
            print(f"\n[Orchestrator iteration {iteration + 1}]")

            response = self.client.chat.completions.create(
                model=ORCHESTRATOR_MODEL,
                messages=messages,
                tools=self.AGENT_TOOL_SCHEMAS,
                tool_choice="auto",
            )

            message = response.choices[0].message

            if message.tool_calls:
                messages.append(message)

                for tool_call in message.tool_calls:
                    agent_name = tool_call.function.name
                    arguments  = json.loads(tool_call.function.arguments)
                    print(f"  → Orchestrator calling: {agent_name}({arguments})")

                    fn     = agent_dispatch[agent_name]
                    result = fn(**arguments)
                    print(f"  ← Result length: {len(result)} chars")

                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tool_call.id,
                        "content":      result,
                    })
            else:
                # Orchestrator gave final summary
                episodic.finish_run(self._run_id, status="success")
                return {
                    "topic":      topic,
                    "research":   self._context_store.get("research", ""),
                    "draft":      self._context_store.get("draft", ""),
                    "summary":    message.content,
                    "session_id": self._session_id,
                    "run_id":     self._run_id,
                    "pipeline":   "llm-driven",
                }

        episodic.finish_run(
            self._run_id, status="error", error="exceeded max iterations",
        )
        return {"error": "Orchestrator loop exceeded max iterations."}