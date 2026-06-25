from typing import List, Dict, Any
from guardrails.models import GuardrailDecision
from memory.db import get_cursor, as_jsonb


def _load_output_policy(policy_name: str) -> Dict[str, Any]:
    """Fetch a JSON config for an output policy from guardrail_policies."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT config
            FROM guardrail_policies
            WHERE name = %s AND kind = 'output'
            """,
            (policy_name,),
        )
        row = cur.fetchone()
    if not row:
        # Default: no constraints
        return {"blocked_terms": [], "required_terms": []}
    return row[0]


def post_llm_output_guard(output_text: str,
                          run_id: str | None = None,
                          session_id: str | None = None,
                          policy_name: str = "default_output_policy") -> GuardrailDecision:
    config = _load_output_policy(policy_name)
    blocked_terms: List[str]  = config.get("blocked_terms", [])
    required_terms: List[str] = config.get("required_terms", [])

    violations: List[str] = []

    lower = output_text.lower()
    for term in blocked_terms:
        if term.lower() in lower:
            violations.append(f"Blocked term: {term}")

    missing_required: List[str] = []
    for term in required_terms:
        if term.lower() not in lower:
            missing_required.append(term)

    action = "allow"
    reason = "Output allowed"

    if violations:
        action = "block"
        reason = "; ".join(violations)
    elif missing_required:
        action = "modify"
        reason = "Missing required terms"

    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO guardrail_events (run_id, session_id, policy_name, layer, action, reason, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                session_id,
                policy_name,
                "post-llm",
                action,
                reason,
                as_jsonb({
                    "blocked_terms": blocked_terms,
                    "required_terms": required_terms,
                    "violations": violations,
                    "missing_required": missing_required,
                }),
            ),
        )

    if action == "block":
        return GuardrailDecision(
            allowed=False,
            action=action,
            reason=reason,
            content=None,
            details={},
        )

    # For "modify" we can auto-append the missing required terms (e.g., disclaimer)
    modified = output_text
    if missing_required:
        # Example: append a disclaimer line
        extra = "\n\n" + " ".join(missing_required)
        modified = output_text + extra

    return GuardrailDecision(
        allowed=True,
        action=action,
        reason=reason,
        content=modified,
        details={},
    )