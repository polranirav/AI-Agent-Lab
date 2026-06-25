"""Orchestrator wiring for the API layer.

Builds a CodeDrivenOrchestrator with its specialist agents. Kept separate from
main.py so it can later grow dependency injection without touching the routes.
"""

from agents.research_agent import ResearchAgent
from agents.writer_agent import WriterAgent
from agents.reviewer_agent import ReviewerAgent
from orchestrator.code_driven import CodeDrivenOrchestrator


def build_orchestrator() -> CodeDrivenOrchestrator:
    research_agent = ResearchAgent()
    writer_agent = WriterAgent()
    reviewer_agent = ReviewerAgent()
    return CodeDrivenOrchestrator(research_agent, writer_agent, reviewer_agent)
