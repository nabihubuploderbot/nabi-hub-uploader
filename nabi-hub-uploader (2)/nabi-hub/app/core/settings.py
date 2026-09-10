"""تنظیمات مرکزی پروژه با pydantic-settings / Central settings via pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """همهٔ متغیرهای محیطی موردنیاز ربات در یک کلاس."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    BOT_TOKEN: str
    MAIN_ADMIN_ID: int
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nabihub"
    REDIS_URL: str | None = None
    WEBHOOK_URL: str | None = None
    WEBHOOK_PATH: str = "/webhook"
    SECRET_TOKEN: str | None = None
    WEBAPP_HOST: str = "0.0.0.0"
    WEBAPP_PORT: int = 8080
    BOT_NAME: str = "Nabi Hub | Uploader"
    DEFAULT_LANG: str = "fa"

    @property
    def is_webhook(self) -> bool:
        return bool(self.WEBHOOK_URL)


cfg = Config()
