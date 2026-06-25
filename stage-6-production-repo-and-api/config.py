"""Backwards-compatible config shim.

Stage 6 centralizes settings in `app/config.py` (Pydantic Settings). This module
re-exports the same values under their original names so existing imports like
`from config import OPENAI_API_KEY` keep working without touching every module.

Prefer `from app.config import settings` in new code.
"""

from app.config import settings

OPENAI_API_KEY     = settings.openai_api_key
ORCHESTRATOR_MODEL = settings.orchestrator_model
AGENT_MODEL        = settings.agent_model
DATABASE_URL       = settings.database_url
