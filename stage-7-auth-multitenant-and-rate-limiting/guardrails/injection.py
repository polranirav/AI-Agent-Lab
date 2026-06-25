import re
from guardrails.models import GuardrailDecision
from memory.db import get_cursor, as_jsonb

# Simple patterns for known injection attempts
INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?previous instructions", re.IGNORECASE),
    re.compile(r"you are no longer", re.IGNORECASE),
    re.compile(r"system prompt", re.IGNORECASE),
    re.compile(r"pretend to", re.IGNORECASE),
]


def pre_llm_injection_guard(input_text: str,
                            run_id: str | None = None,
                            session_id: str | None = None,
                            policy_name: str = "default_injection_policy") -> GuardrailDecision:
    """Detect obvious prompt-injection attempts and block or flag them."""
    for pattern in INJECTION_PATTERNS:
        if pattern.search(input_text):
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
                        "pre-llm",
                        "block",
                        "Prompt injection pattern detected",
                        as_jsonb({"pattern": pattern.pattern}),
                    ),
                )
            return GuardrailDecision(
                allowed=False,
                action="block",
                reason="Prompt injection detected",
                content=None,
                details={"pattern": pattern.pattern},
            )

    return GuardrailDecision(
        allowed=True,
        action="allow",
        reason="No injection pattern detected",
        content=input_text,
        details={},
    )