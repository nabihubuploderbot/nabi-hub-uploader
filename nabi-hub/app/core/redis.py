"""مدیریت ردیس برای FSM و صف‌ها / Redis manager for FSM & queues."""
import redis.asyncio as aioredis
from loguru import logger

from app.core.settings import cfg


class RedisManager:
    """پوشش حرفه‌ای روی کلاینت Async Redis."""

    def __init__(self, client: aioredis.Redis | None = None) -> None:
        self.client = client

    @classmethod
    async def connect(cls, url: str | None) -> "RedisManager":
        """اگر REDIS_URL تنظیم نشده باشد، None برمی‌گردد (حالت فاقد ردیس)."""
        if not url:
            logger.warning("REDIS_URL تنظیم نشده - FSM روی حافظهٔ رم اجرا می‌شود.")
            return cls(None)
        try:
            client = aioredis.from_url(url, decode_responses=True)
            await client.ping()
            logger.info("✅ اتصال Redis برقرار شد.")
            return cls(client)
        except Exception as e:  # noqa: BLE001
            logger.error(f"خطا در اتصال Redis: {e}")
            return cls(None)

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()

    @staticmethod
    def for_fsm():
        """ساخت Storage مناسب برای FSM بر اساس وجود یا نبود ردیس."""
        if cfg.REDIS_URL:
            try:
                from aiogram.fsm.storage.redis import RedisStorage

                return RedisStorage.from_url(cfg.REDIS_URL)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"RedisStorage ناموفق → MemoryStorage: {e}")
        from aiogram.fsm.storage.memory import MemoryStorage

        return MemoryStorage()
