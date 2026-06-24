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

def execute(tool_name: str, arguments: dict,
            user_id: str = None,
            run_id: str = None,
            session_id: str = None) -> str:
    """
    Execute a tool by name.

    Stage 4: when a user_id is provided, every tool call first passes through
    the runtime/tool guardrail (RBAC + approval). Tools are filtered BEFORE
    they run and every invocation is logged to guardrail_events.
    """
    if tool_name not in REGISTRY:
        return f"Error: unknown tool '{tool_name}'"

    # Runtime/tool guardrail (only enforced when we know who the user is).
    if user_id is not None:
        from guardrails import service as guardrails
        decision = guardrails.check_tool_guard(
            tool_name, user_id, run_id=run_id, session_id=session_id,
        )
        if not decision.allowed:
            if decision.action == "escalate":
                return "This action requires approval from a human operator."
            return f"Tool call blocked by guardrails: {decision.reason}"

    _, run_fn = REGISTRY[tool_name]
    try:
        return run_fn(**arguments)
    except Exception as e:
        return f"Tool execution error: {e}"