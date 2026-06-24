import os
from dotenv import load_dotenv


load_dotenv()

OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "gpt-4o")
AGENT_MODEL        = os.getenv("AGENT_MODEL", "gpt-4o-mini")
DATABASE_URL       = os.getenv("DATABASE_URL")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env file")
