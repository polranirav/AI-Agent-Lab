"""Runtime tool guard (RBAC + approval checks for tool calls)."""

from guardrails.service import check_tool_guard
from guardrails.models import GuardrailDecision


def guard_tool(tool_name: str, user_id: str,
               run_id=None, session_id=None) -> GuardrailDecision:
    return check_tool_guard(tool_name, user_id, run_id=run_id, session_id=session_id)
