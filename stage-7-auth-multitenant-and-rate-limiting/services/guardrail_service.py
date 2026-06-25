"""Thin façade over the guardrails service.

Live enforcement still happens inside the agents and tools (as wired in Stage 4);
this façade exposes the same checks to other callers (e.g. an API that wants to
pre-screen input before spending an orchestrator run).
"""

from guardrails import service as _guardrails
from guardrails.models import GuardrailDecision


def screen_input(text: str, run_id=None, session_id=None) -> GuardrailDecision:
    return _guardrails.apply_pre_llm_guards(text, run_id=run_id, session_id=session_id)


def screen_output(text: str, run_id=None, session_id=None,
                  policy_name: str = "creator_brand_policy") -> GuardrailDecision:
    return _guardrails.apply_post_llm_guards(
        text, run_id=run_id, session_id=session_id, policy_name=policy_name,
    )


def check_tool(tool_name: str, user_id: str,
               run_id=None, session_id=None) -> GuardrailDecision:
    return _guardrails.check_tool_guard(
        tool_name, user_id, run_id=run_id, session_id=session_id,
    )
