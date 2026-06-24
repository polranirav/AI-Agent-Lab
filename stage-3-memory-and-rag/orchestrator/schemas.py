from pydantic import BaseModel


class ResearchOutput(BaseModel):
    """Structured output from ResearchAgent."""
    summary:    str
    key_points: list[str]
    facts:      list[str]


class WritingOutput(BaseModel):
    """Structured output from WriterAgent."""
    title:   str
    content: str
    word_count: int


class ReviewOutput(BaseModel):
    """Structured output from ReviewerAgent."""
    verdict:      str           # "APPROVE", "REVISE", or "REJECT"
    strengths:    list[str]
    improvements: list[str]
    suggested_rewrite: str


class CampaignPlan(BaseModel):
    """
    Future use: structured output for Creator Orchestrator.
    Shown here to preview where Stage 2 leads.
    """
    topic:           str
    target_platforms: list[str]
    proposed_clips:  list[str]
    suggested_posts: list[str]