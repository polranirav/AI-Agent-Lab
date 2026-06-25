"""
Guardrail & Policy layer for Stage 4.

Three layers of defense, all DB-backed and logged to `guardrail_events`:
  - pre-LLM  : PII redaction + prompt-injection detection (input side)
  - post-LLM : brand/content policy enforcement (output side)
  - tool     : RBAC + approval checks around tool calls (action side)

Orchestrators and agents import `guardrails.service` — never the
individual modules or SQL directly.
"""

from guardrails import models, pii, injection, policy, tools, service

__all__ = ["models", "pii", "injection", "policy", "tools", "service"]
