import json
import logging
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Defaults to SQLite for zero-config local dev.
    # Set DATABASE_URL=postgresql+asyncpg://user:pass@host/db for production.
    DATABASE_URL: str = "sqlite+aiosqlite:///./draw_imposter.db"
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        """Accept JSON array, single URL, comma-separated, or already a list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try JSON array first
            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass
            # Single URL (no brackets)
            if "://" in v or v.startswith("http"):
                return [v]
            # Comma-separated
            if "," in v:
                parts = [p.strip().strip('"').strip("'") for p in v.split(",")]
                return [p for p in parts if p]
            # Single bare value
            return [v.strip()]
        logger.warning("Unexpected type for CORS_ORIGINS: %s — using default", type(v).__name__)
        return ["http://localhost:5173"]


settings = Settings()
logger.info("CORS_ORIGINS = %s", settings.CORS_ORIGINS)
