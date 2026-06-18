import json
from openai import OpenAI
from config import OPENAI_API_KEY
from tools.registry import get_schemas, execute


class BaseAgent:
    """
    Base class for all specialist agents.
    Contains the shared agent loop from Stage 1.
    Subclasses define:
      - name: agent identifier
      - system_prompt: behavior and role
      - allowed_tools: which tools this agent can use
      - model: which LLM model to use
    """

    name: str = "BaseAgent"
    system_prompt: str = "You are a helpful assistant."
    allowed_tools: list[str] = []  # empty = no tools
    model: str = "gpt-4o-mini"
    max_iterations: int = 6

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def run(self, user_message: str, context: str = "") -> str:
        """
        Run this agent on a user message.
        Optional context is appended to the system prompt.
        Returns the agent's final text response.
        """
        system = self.system_prompt
        if context:
            system += f"\n\n--- CONTEXT PROVIDED ---\n{context}"

        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user_message},
        ]

        tools = get_schemas(self.allowed_tools) if self.allowed_tools else []
        call_kwargs = {"model": self.model, "messages": messages}
        if tools:
            call_kwargs["tools"] = tools
            call_kwargs["tool_choice"] = "auto"

        for iteration in range(self.max_iterations):
            response = self.client.chat.completions.create(**call_kwargs)
            message = response.choices[0].message

            if message.tool_calls:
                # Execute tools and feed results back
                messages.append(message)
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    result    = execute(tool_name, arguments)
                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tool_call.id,
                        "content":      result,
                    })
                call_kwargs["messages"] = messages
            else:
                return message.content or ""

        return "Error: agent loop exceeded max iterations."