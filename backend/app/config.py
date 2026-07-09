from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://rca:rca@db:5432/rca"
    redis_url: str = "redis://redis:6379/0"

    anthropic_api_key: str = ""
    triage_model: str = "claude-haiku-4-5-20251001"
    rca_model: str = "claude-sonnet-5"
    max_agent_iterations: int = 8

    slack_bot_token: str = ""

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
