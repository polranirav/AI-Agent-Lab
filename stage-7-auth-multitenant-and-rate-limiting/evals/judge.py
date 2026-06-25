"""LLM-as-a-judge evaluator for subjective quality (relevance, brand/tone)."""

import json
from typing import Optional

from openai import OpenAI

from config import OPENAI_API_KEY, AGENT_MODEL
from evals.store import save_eval_result

client = OpenAI(api_key=OPENAI_API_KEY)

JUDGE_PROMPT = """You are an expert marketing editor.

You will be given:
- A content brief.
- A generated marketing asset.

Evaluate the asset on a scale of 1 to 5 for:
- Relevance to the brief.
- Brand tone and style match.

Return a JSON object with this exact format:
{"relevance": <1-5>, "tone": <1-5>, "overall": <1-5>, "comments": "..."}
"""


def judge_brand_fit(run_id: str,
                    session_id: Optional[str],
                    brief: str,
                    content: str,
                    target: str) -> float:
    """Use a cheap LLM judge to score relevance & tone for a piece of content."""
    messages = [
        {"role": "system", "content": JUDGE_PROMPT},
        {"role": "user", "content": f"BRIEF:\n{brief}\n\nCONTENT:\n{content}"},
    ]

    response = client.chat.completions.create(
        model=AGENT_MODEL,  # cheap judge model
        messages=messages,
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content)
    overall = float(data.get("overall", 0))

    save_eval_result(
        run_id=run_id,
        session_id=session_id,
        evaluator="brand_fit_judge",
        scope="agent",
        target=target,
        score=overall,
        label="good" if overall >= 4 else "ok" if overall >= 3 else "bad",
        details=data,
    )
    return overall
