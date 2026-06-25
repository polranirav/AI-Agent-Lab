"""Pre-LLM input guard (PII redaction + prompt-injection detection)."""

from guardrails.service import apply_pre_llm_guards
from guardrails.models import GuardrailDecision


def guard_input(text: str, run_id=None, session_id=None) -> GuardrailDecision:
    return apply_pre_llm_guards(text, run_id=run_id, session_id=session_id)
