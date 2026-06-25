"""Post-LLM content filter (brand/content policy enforcement)."""

from guardrails.service import apply_post_llm_guards
from guardrails.models import GuardrailDecision


def filter_output(text: str, run_id=None, session_id=None,
                  policy_name: str = "creator_brand_policy") -> GuardrailDecision:
    return apply_post_llm_guards(
        text, run_id=run_id, session_id=session_id, policy_name=policy_name,
    )
