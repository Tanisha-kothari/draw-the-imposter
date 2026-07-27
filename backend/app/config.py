from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


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


settings = Settings()
