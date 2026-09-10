"""Rate Limit ساده بر اساس فاصلهٔ زمانی / Simple time-gap based throttling."""
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from loguru import logger

THROTTLE_SECONDS = 0.5


class ThrottlingMiddleware(BaseMiddleware):
    """جلوی اسپم کاربران را می‌گیرد (۰/۵ ثانیه فاصلهٔ حداقلی)."""

    def __init__(self) -> None:
        self._last: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Any], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        now = time.monotonic()
        last = self._last.get(user.id, 0.0)
        if now - last < THROTTLE_SECONDS:
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer("⏳ کمی آرام‌تر!", show_alert=False)
                except Exception:  # noqa: BLE001
                    pass
            logger.debug(f"throttled user={user.id}")
            return None  # آپdt نادیده گرفته می‌شود
        self._last[user.id] = now
        return await handler(event, data)
