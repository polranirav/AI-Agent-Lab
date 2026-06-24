import json
from typing import Optional

from openai import OpenAI

from config import OPENAI_API_KEY
from tools.registry import get_schemas, execute
from memory import short_term, episodic


class BaseAgent:
    """
    Base class for all specialist agents.
    Contains the shared agent loop from Stage 1, now wired into memory.

    Subclasses define:
      - name: agent identifier
      - system_prompt: behavior and role
      - allowed_tools: which tools this agent can use
      - model: which LLM model to use

    Stage 3 additions:
      - session_id ties an agent run to short-term memory (sessions/messages).
      - run_id ties an agent run to episodic memory (runs/events).
      - Every message is persisted; recent history primes the system prompt.
    """

    name: str = "BaseAgent"
    system_prompt: str = "You are a helpful assistant."
    allowed_tools: list[str] = []  # empty = no tools
    model: str = "gpt-4o-mini"
    max_iterations: int = 6

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def run(self, user_message: str, context: str = "",
            session_id: Optional[str] = None,
            run_id: Optional[str] = None) -> str:
        """
        Run this agent on a user message, optionally attached to a session/run.
        Optional context is appended to the system prompt.
        Returns the agent's final text response.
        """
        # If no session provided, create one so memory is always recorded.
        if session_id is None:
            session_id = short_term.create_session(topic=self.name)

        # Episodic: log agent start.
        if run_id is not None:
            episodic.log_event(
                run_id,
                event_type="agent_start",
                message=f"{self.name} starting",
                agent_name=self.name,
                payload={"session_id": session_id},
            )

        system = self.system_prompt
        if context:
            system += f"\n\n--- CONTEXT PROVIDED ---\n{context}"

        # Short-term: include recent history to give continuity across calls.
        history_messages = short_term.get_recent_messages(session_id, limit=10)
        history_text = short_term.summarize_history_text(history_messages)
        if history_text:
            system += f"\n\n--- RECENT HISTORY ---\n{history_text}"

        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user_message},
        ]

        # Persist the system + user messages.
        short_term.append_message(session_id, "system", system)
        short_term.append_message(session_id, "user", user_message)

        tools = get_schemas(self.allowed_tools) if self.allowed_tools else []
        call_kwargs = {"model": self.model, "messages": messages}
        if tools:
            call_kwargs["tools"] = tools
            call_kwargs["tool_choice"] = "auto"

        for iteration in range(self.max_iterations):
            response = self.client.chat.completions.create(**call_kwargs)
            message = response.choices[0].message

            if message.tool_calls:
                # Execute tools and feed results back.
                messages.append(message)
                short_term.append_message(
                    session_id, "assistant",
                    json.dumps({"tool_calls": [tc.function.name
                                               for tc in message.tool_calls]}),
                )

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    if run_id is not None:
                        episodic.log_event(
                            run_id,
                            event_type="tool_call",
                            message=f"{self.name} calling {tool_name}",
                            agent_name=self.name,
                            payload={"arguments": arguments},
                        )

                    result = execute(tool_name, arguments)
                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tool_call.id,
                        "content":      result,
                    })
                    short_term.append_message(
                        session_id, "tool", result, {"tool": tool_name},
                    )
                call_kwargs["messages"] = messages
            else:
                final = message.content or ""
                short_term.append_message(session_id, "assistant", final)

                if run_id is not None:
                    episodic.log_event(
                        run_id,
                        event_type="agent_end",
                        message=f"{self.name} finished",
                        agent_name=self.name,
                        payload={"final_preview": final[:200]},
                    )
                return final

        if run_id is not None:
            episodic.log_event(
                run_id,
                event_type="agent_error",
                message=f"{self.name} exceeded max iterations",
                agent_name=self.name,
                payload={},
            )
        return "Error: agent loop exceeded max iterations."
