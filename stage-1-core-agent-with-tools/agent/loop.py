import json
from openai import OpenAI
from config import OPENAI_API_KEY, MODEL_NAME
from tools.registry import get_all_schemas, execute
from agent.prompts import SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)
MAX_ITERATIONS = 10  # safety limit - prevents infinite loops


def run_agent(user_message: str) -> str:
    """
    Run the single-agent loop.

    1. Build message list (System + User)
    2. Call Model with tool schemas.
    3. if model returns tool_calls -> execute each -> add result -> loop.
    4. if model returns text -> return it.
    """

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_message},
    ]
    tools = get_all_schemas()

    for iteration in range(MAX_ITERATIONS):
        print(f"\n [Loop iteration {iteration + 1}]")

        # --- call the model ---
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message
        print(assistant_message)

        # --- check: did the model want to call tools? ---
        if assistant_message.tool_calls:
            print(f"  Model requested {len(assistant_message.tool_calls)} tool call(s):")

            # add the assistant's tool-call message to history
            messages.append(assistant_message)

            # execute each tool call and add results
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                print(f"      -> calling '{tool_name}' with {arguments}")
                result = execute(tool_name, arguments)
                print(f"      <- Result: {result}")

                # add tool result to messages (role = "tool")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": result,
                    }
                )

            # continue the loop - feed results back to model
        else:
            # --- model gave a final text answer ---
            final_answer = assistant_message.content
            print(f"\n [Final Answer after {iteration + 1} iteration(s)]")
            return final_answer

    return "Error: Maximum iterations reached without a final answer"
