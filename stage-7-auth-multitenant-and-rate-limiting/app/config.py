"""Central application settings.

Loads environment variables in ONE place using Pydantic settings, the standard
pattern for production LLM apps. Import `settings` everywhere instead of calling
os.getenv directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Required
    openai_api_key: str
    database_url: str  # kept as str so psycopg gets the raw DSN unchanged

    # Models (sensible defaults)
    orchestrator_model: str = "gpt-4o"
    agent_model: str = "gpt-4o-mini"

    # Auth (JWT). Override jwt_secret_key in production via env.
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Rate limiting (per tenant+user, per minute).
    rate_limit_per_minute: int = 60

    # Future: anthropic_api_key, gemini_api_key, feature flags, etc.

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
