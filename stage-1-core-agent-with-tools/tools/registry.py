from tools import calculator, weather, word_count

# All registered tools: maps tool name → (schema, run_function)
REGISTRY = {
    "calculator": (calculator.SCHEMA, calculator.run),
    "get_weather": (weather.SCHEMA,   weather.run),
    "word_count":  (word_count.SCHEMA, word_count.run),
}

def get_all_schemas() -> list:
    """Return all tool schemas — passed to the model so it knows what's available."""
    return [schema for schema, _ in REGISTRY.values()]

def execute(tool_name: str, arguments: dict) -> str:
    """Execute a tool by name with the given arguments."""
    if tool_name not in REGISTRY:
        return f"Error: unknown tool '{tool_name}'"
    _, run_fn = REGISTRY[tool_name]
    try:
        return run_fn(**arguments)
    except Exception as e:
        return f"Tool execution error: {e}"