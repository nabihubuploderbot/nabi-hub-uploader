"""تنظیمات مرکزی پروژه با pydantic-settings / Central settings via pydantic-settings."""
import os

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

    # پیش‌فرض: polling (همه‌جا کار می‌کند).
    # برای Webhook صریحاً RUN_MODE=webhook + WEBHOOK_URL را ست کنید.
    RUN_MODE: str = "polling"

    WEBHOOK_URL: str | None = None
    WEBHOOK_PATH: str = "/webhook"
    SECRET_TOKEN: str | None = None
    WEBAPP_HOST: str = "0.0.0.0"
    # 0 یعنی از متغیر PORT (مثل Railway) استفاده کن، وگرنه 8080
    WEBAPP_PORT: int = 0
    BOT_NAME: str = "Nabi Hub | Uploader"
    DEFAULT_LANG: str = "fa"

    # حالت تست اتصال: اگر 1 باشد، /start یک پیام «اتصال برقرار است» می‌فرستد
    DEBUG_ECHO: bool = False

    @property
    def run_mode(self) -> str:
        """حالت نهایی اجرا: polling یا webhook / Final run mode."""
        if self.RUN_MODE in ("polling", "webhook"):
            return self.RUN_MODE
        return "webhook" if self.WEBHOOK_URL else "polling"

    @property
    def webapp_port(self) -> int:
        """پورت وب‌سرور؛ 0 یعنی از متغیر محیطی PORT (Railway) بخوان."""
        if self.WEBAPP_PORT == 0:
            return int(os.getenv("PORT", "8080"))
        return self.WEBAPP_PORT


cfg = Config()
