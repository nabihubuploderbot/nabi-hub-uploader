"""
config.py — Application configuration using pydantic-settings.

All environment variables are loaded from .env file or system environment.
"""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Central configuration class.
    Reads from .env file and environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Telegram ──────────────────────────────────────
    BOT_TOKEN: str = Field(..., description="Telegram Bot Token")
    MAIN_ADMIN_ID: int = Field(..., description="Main admin Telegram user ID")

    # ── Database ──────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/nabi_hub",
        description="PostgreSQL async connection string",
    )

    # ── Redis ─────────────────────────────────────────
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # ── Webhook ───────────────────────────────────────
    USE_WEBHOOK: bool = Field(default=False, description="Use webhook instead of polling")
    WEBHOOK_URL: str = Field(default="", description="Public webhook URL")
    WEBHOOK_PATH: str = Field(default="/webhook", description="Webhook endpoint path")
    SECRET_TOKEN: str = Field(default="", description="Webhook secret token for security")
    WEBAPP_HOST: str = Field(default="0.0.0.0", description="Webhook server host")
    WEBAPP_PORT: int = Field(default=8000, description="Webhook server port")

    # ── Logging ───────────────────────────────────────
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # ── Paths ─────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parent

    @property
    def webhook_url_full(self) -> str:
        """Full webhook URL including path."""
        return f"{self.WEBHOOK_URL.rstrip('/')}{self.WEBHOOK_PATH}"


# Singleton instance
settings = Settings()
