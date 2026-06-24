from tools import search, calculator

REGISTRY = {
    "web_search":  (search.SCHEMA,     search.run),
    "calculator":  (calculator.SCHEMA, calculator.run),
}

def get_schemas(tool_names: list[str] = None) -> list:
    """
    Return tool schemas — optionally filtered by name.
    This is the first taste of per-agent tool access control:
    each agent only gets the tools it needs.
    """
    if tool_names is None:
        return [schema for schema, _ in REGISTRY.values()]
    return [
        REGISTRY[name][0]
        for name in tool_names
        if name in REGISTRY
    ]

def execute(tool_name: str, arguments: dict) -> str:
    if tool_name not in REGISTRY:
        return f"Error: unknown tool '{tool_name}'"
    _, run_fn = REGISTRY[tool_name]
    try:
        return run_fn(**arguments)
    except Exception as e:
        return f"Tool execution error: {e}"