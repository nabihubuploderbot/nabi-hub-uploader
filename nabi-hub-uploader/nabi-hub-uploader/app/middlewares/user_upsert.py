"""ثبت/به‌روزرسانی خودکار کاربر + چک روشن بودن ربات / Auto user upsert + power check."""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from loguru import logger

from app.core.db import Database
from app.services.settings_service import SettingsService
from app.services.user_service import UserService


class UserUpsertMiddleware(BaseMiddleware):
    """هر کاربر جدید را ثبت و کاربر موجود را به‌روزرسانی می‌کند.

    اگر ربات خاموش باشد، فقط /start پاس داده می‌شود.
    """

    async def __call__(
        self,
        handler: Callable[[Any], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        db: Database | None = data.get("db")
        tg_user = data.get("event_from_user")
        if db is None or tg_user is None:
            return await handler(event, data)

        async with db.session_factory() as session:
            service = UserService(session)
            user = await service.get_or_create(
                telegram_id=tg_user.id,
                username=tg_user.username,
                full_name=tg_user.full_name or "",
            )
            await session.commit()

            # چک خاموش/روشن بودن ربات (فقط برای پیام‌ها، نه دکمه‌های ادمین)
            from app.locales.fa import TEXTS

            settings = await SettingsService(session).get()
            is_start = isinstance(event, Message) and (event.text or "").startswith("/start")
            if not settings.bot_enabled and not is_start and not data.get("is_admin"):
                if isinstance(event, Message):
                    await event.answer(TEXTS["bot_disabled"])
                return None

            data["user"] = user
            return await handler(event, data)
