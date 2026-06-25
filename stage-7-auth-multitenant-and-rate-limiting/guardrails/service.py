from typing import Optional
from guardrails.models import GuardrailDecision
from guardrails import pii, injection, policy as policy_mod, tools as tools_mod


def apply_pre_llm_guards(input_text: str,
                         run_id: str | None = None,
                         session_id: str | None = None) -> GuardrailDecision:
    """Apply pre-LLM guardrails (PII + injection)."""
    # 1) PII redaction
    pii_decision = pii.pre_llm_pii_guard(input_text, run_id, session_id)
    if not pii_decision.allowed:
        return pii_decision

    # 2) Injection detection
    inj_decision = injection.pre_llm_injection_guard(pii_decision.content or input_text,
                                                     run_id, session_id)
    if not inj_decision.allowed:
        return inj_decision

    # If both allow, pass forward the redacted text
    return GuardrailDecision(
        allowed=True,
        action="allow",
        reason="Pre-LLM checks passed",
        content=inj_decision.content or pii_decision.content or input_text,
    )


def apply_post_llm_guards(output_text: str,
                          run_id: str | None = None,
                          session_id: str | None = None,
                          policy_name: str = "creator_brand_policy") -> GuardrailDecision:
    """Apply post-LLM content/brand policy guardrails."""
    return policy_mod.post_llm_output_guard(output_text, run_id, session_id, policy_name)


def check_tool_guard(tool_name: str,
                     user_id: str,
                     run_id: str | None = None,
                     session_id: str | None = None) -> GuardrailDecision:
    """Check runtime/tool guardrails for a specific tool call."""
    return tools_mod.check_tool_permission(tool_name, user_id, run_id, session_id)