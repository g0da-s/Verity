"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Required API keys
    anthropic_api_key: str
    pubmed_email: str

    # Optional LangSmith settings
    langsmith_api_key: str | None = None
    langsmith_project: str = "truthcheck"
    langsmith_tracing: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/truthcheck.db"

    # API Configuration
    cors_origins: str = "http://localhost:3000"  # Comma-separated string
    host: str = "0.0.0.0"
    port: int = 8000

    # Application settings
    app_name: str = "TruthCheck"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
