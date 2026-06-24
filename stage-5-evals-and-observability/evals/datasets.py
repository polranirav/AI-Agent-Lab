"""Curated offline evaluation datasets (the prompts the harness replays)."""

from typing import Any, Dict, List


def offline_eval_dataset() -> List[Dict[str, Any]]:
    """Hard-coded small dataset for now. Later: load from JSON/CSV."""
    return [
        {
            "topic": "Shorts: 60-second explainer on API rate limiting",
            "brief": "Audience: junior backend devs. Tone: friendly, concise, no hype.",
        },
        {
            "topic": "YouTube: 8-minute video on Postgres + pgvector for RAG",
            "brief": "Audience: indie hackers. Tone: practical, code-focused, minimal fluff.",
        },
    ]
