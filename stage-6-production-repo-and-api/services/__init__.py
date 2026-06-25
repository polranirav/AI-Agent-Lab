"""Service layer.

Thin façades the API and other callers use instead of reaching into internal
packages directly. Keeps a clean boundary between transport (HTTP) and domain
logic (memory, guardrails, evals).
"""
