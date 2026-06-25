"""Agent unit tests — configuration only, no live LLM calls."""

from agents.research_agent import ResearchAgent
from agents.writer_agent import WriterAgent
from agents.reviewer_agent import ReviewerAgent


def test_research_agent_uses_web_search():
    agent = ResearchAgent()
    assert agent.name == "ResearchAgent"
    assert "web_search" in agent.allowed_tools


def test_writer_and_reviewer_have_no_tools():
    assert WriterAgent().allowed_tools == []
    assert ReviewerAgent().allowed_tools == []


def test_agents_have_system_prompts():
    for cls in (ResearchAgent, WriterAgent, ReviewerAgent):
        assert cls().system_prompt.strip()
