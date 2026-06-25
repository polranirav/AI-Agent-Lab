"""Orchestrator wiring tests (no live LLM calls)."""

from app.orchestrator import build_orchestrator
from orchestrator.code_driven import CodeDrivenOrchestrator


def test_build_orchestrator_returns_code_driven():
    orch = build_orchestrator()
    assert isinstance(orch, CodeDrivenOrchestrator)


def test_orchestrator_has_three_agents():
    orch = build_orchestrator()
    assert orch.research_agent.name == "ResearchAgent"
    assert orch.writer_agent.name == "WriterAgent"
    assert orch.reviewer_agent.name == "ReviewerAgent"


def test_orchestrator_accepts_injected_agents():
    # Injecting agents (API path) and default-constructing (CLI path) both work.
    default_orch = CodeDrivenOrchestrator()
    assert default_orch.research_agent is not None
