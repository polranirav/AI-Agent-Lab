import os
from dotenv import load_dotenv


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL")
AGENT_MODEL = os.getenv("AGENT_MODEL")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file")
