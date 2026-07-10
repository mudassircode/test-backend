"""
Centralized configuration. Loads from .env and validates on import.
If something is missing, the app fails at STARTUP with a clear error —
not mid-request with a vague "we don't have ..." error.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- OpenAI ---
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key, starts with sk-")
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSIONS: int = 1536  # text-embedding-3-small default

    # --- Database (Neon Postgres) ---
    DATABASE_URL: str = Field(..., description="postgresql+asyncpg://user:pass@host/db")

    # --- App ---
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        if not v or not v.startswith("sk-"):
            raise ValueError(
                "OPENAI_API_KEY is missing or malformed. "
                "It must start with 'sk-'. Check your .env file."
            )
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the 'postgresql+asyncpg://' scheme "
                "(async driver required). Got a different scheme."
            )
        return v

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


# Instantiated once, imported everywhere. This line will CRASH IMMEDIATELY
# with a clear message if .env is misconfigured — that's intentional.
settings = Settings()
