import re
from typing import Tuple, Dict
from guardrails.models import GuardrailDecision
from memory import episodic

# Simple regex patterns for common PII types
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"\+?[0-9][0-9\- ]{7,}[0-9]")


def redact_pii(text: str) -> Tuple[str, Dict[str, str]]:
    """Redact basic PII and return (redacted_text, redaction_map)."""
    redaction_map: Dict[str, str] = {}

    def _replace(pattern, placeholder_type):
        nonlocal text
        for match in pattern.findall(text):
            placeholder = f"[{placeholder_type}_REDACTED]"
            text = text.replace(match, placeholder)
            redaction_map[match] = placeholder

    _replace(EMAIL_REGEX, "EMAIL")
    _replace(PHONE_REGEX, "PHONE")
    return text, redaction_map


def pre_llm_pii_guard(input_text: str,
                      run_id: str | None = None,
                      session_id: str | None = None,
                      policy_name: str = "default_pii_policy") -> GuardrailDecision:
    """Pre-LLM PII guardrail: redact obvious PII before it reaches the model."""
    redacted, mapping = redact_pii(input_text)

    if mapping:
        # Log guardrail event
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
                    policy_name,
                    "pre-llm",
                    "redact",
                    "PII redacted in input",
                    as_jsonb({"mapping": mapping}),
                ),
            )

    return GuardrailDecision(
        allowed=True,
        action="redact" if mapping else "allow",
        reason="PII redacted" if mapping else "No PII detected",
        content=redacted,
        details={"mapping": mapping},
    )