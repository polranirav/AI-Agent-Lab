"""Pydantic request/response schemas for the HTTP API.

These make the API self-documenting (FastAPI auto-generates OpenAPI docs).
"""

from typing import List, Optional

from pydantic import BaseModel


class OrchestrateRequest(BaseModel):
    topic: str
    brief: str = ""
    user_id: Optional[str] = None


class Artifact(BaseModel):
    kind: str  # 'clip', 'post', 'email'
    content: str


class OrchestrateResponse(BaseModel):
    run_id: str
    session_id: str
    artifacts: List[Artifact]
    metrics: dict
