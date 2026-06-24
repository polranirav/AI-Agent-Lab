from typing import Optional, Dict, Any
from memory.db import get_cursor
from guardrails.models import GuardrailDecision


def _get_role_ids_for_user(user_id: str) -> list[int]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT role_id FROM user_roles WHERE user_id = %s
            """,
            (user_id,),
        )
        rows = cur.fetchall()
    return [row[0] for row in rows]


def check_tool_permission(tool_name: str,
                          user_id: str,
                          run_id: str | None = None,
                          session_id: str | None = None) -> GuardrailDecision:
    """Check if a given user is allowed to invoke a tool, and whether approval is needed."""
    role_ids = _get_role_ids_for_user(user_id)
    if not role_ids:
        # No roles → deny by default
        _log_tool_guardrail(run_id, session_id, tool_name, "block", "No roles assigned", {})
        return GuardrailDecision(
            allowed=False,
            action="block",
            reason="User has no roles",
        )

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT allowed, require_approval
            FROM tool_policies
            WHERE tool_name = %s AND role_id = ANY(%s)
            """,
            (tool_name, role_ids),
        )
        rows = cur.fetchall()

    if not rows:
        _log_tool_guardrail(run_id, session_id, tool_name, "block", "No policy for user roles", {})
        return GuardrailDecision(
            allowed=False,
            action="block",
            reason="No tool policy for user roles",
        )

    # If any policy row allows without approval, allow
    for allowed, require_approval in rows:
        if allowed and not require_approval:
            _log_tool_guardrail(run_id, session_id, tool_name, "allow", "Allowed by policy", {})
            return GuardrailDecision(
                allowed=True,
                action="allow",
                reason="Allowed by policy",
            )

    # Otherwise, either all require approval or some deny
    # Simplified: require approval
    _log_tool_guardrail(run_id, session_id, tool_name, "escalate", "Requires approval", {})
    return GuardrailDecision(
        allowed=False,
        action="escalate",
        reason="Tool use requires approval",
    )


def _log_tool_guardrail(run_id: str | None,
                        session_id: str | None,
                        tool_name: str,
                        action: str,
                        reason: str,
                        details: Dict[str, Any]) -> None:
    from memory.db import get_cursor, as_jsonb
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO guardrail_events (run_id, session_id, policy_name, layer, action, reason, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                session_id,
                f"tool_policy:{tool_name}",
                "tool",
                action,
                reason,
                as_jsonb(details),
            ),
        )