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

    # Database
    # Defaults to SQLite for local development.
    # Override with DATABASE_URL on Render when using PostgreSQL.
    DATABASE_URL: str = "sqlite+aiosqlite:///./draw_imposter.db"

    # Security
    SECRET_KEY: str = "change-me-in-production"

    # Default CORS origins.
    # If CORS_ORIGINS is provided as an environment variable,
    # it will override this list.
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "https://draw-the-imp-git-261c37-kotharitanishanilesh-gmailcoms-projects.vercel.app",
        "https://draw-the-imposter-4yyit4g7j.vercel.app",
        "https://draw-the-imposter-as510yw2c.vercel.app",
    ]

    # Optional Supabase configuration
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        """
        Accept any of the following formats:

        JSON:
        ["https://site.com","http://localhost:5173"]

        Single URL:
        https://site.com

        Comma separated:
        https://site.com,http://localhost:5173

        Python list:
        ["https://site.com", "http://localhost:5173"]
        """

        if isinstance(v, list):
            return v

        if isinstance(v, str):
            # JSON array
            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass

            # Single URL
            if v.startswith("http://") or v.startswith("https://"):
                return [v]

            # Comma separated
            if "," in v:
                return [
                    item.strip().strip('"').strip("'")
                    for item in v.split(",")
                    if item.strip()
                ]

            return [v.strip()]

        logger.warning(
            "Unexpected CORS_ORIGINS type: %s. Falling back to defaults.",
            type(v).__name__,
        )

        return [
            "http://localhost:5173",
            "https://draw-the-imp-git-261c37-kotharitanishanilesh-gmailcoms-projects.vercel.app",
            "https://draw-the-imposter-4yyit4g7j.vercel.app",
            "https://draw-the-imposter-as510yw2c.vercel.app",
        ]


settings = Settings()

logger.info("========================================")
logger.info("DATABASE_URL = %s", settings.DATABASE_URL)
logger.info("CORS_ORIGINS = %s", settings.CORS_ORIGINS)
logger.info("SECRET_KEY configured = %s", settings.SECRET_KEY != "change-me-in-production")
logger.info("========================================")