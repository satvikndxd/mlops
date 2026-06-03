"""Application configuration via environment variables.

All settings are read from the environment with the ``AGENTFORGE_`` prefix
(e.g. ``AGENTFORGE_DATABASE_URL``) and optionally a local ``.env`` file.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENTFORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "AgentForge"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/v1"

    # Database — defaults to a local SQLite file so the steel thread runs with
    # zero external dependencies; docker-compose overrides with PostgreSQL.
    database_url: str = "sqlite:///./agentforge.db"

    # CORS — the Next.js dashboard origin(s).
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Default organization used by unauthenticated trace ingestion in Phase 0.
    default_org_slug: str = "default"
    default_org_name: str = "Default Organization"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
