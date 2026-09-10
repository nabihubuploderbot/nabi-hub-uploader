"""قفل عضویت اجباری / Force-join middleware.

اگر قفل فعال باشد، همهٔ درخواست‌ها (به‌جز /start و /cancel) تا عضویت
کاربر در همهٔ کانال‌ها بلاک می‌شوند و پیام قفل + دکمهٔ «بررسی مجدد» ارسال می‌شود.
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message

from loguru import logger

from app.keyboards.locks import force_join_keyboard
from app.locales.fa import TEXTS

# دستوراتی که حتی با قفل هم باید پاس شوند
ALLOWED_COMMANDS = {"/start", "/cancel"}


class ForceJoinMiddleware(BaseMiddleware):
    """چک عضویت کاربر در کانال‌های اجباری + قفل واکنش."""

    async def __call__(
        self,
        handler: Callable[[Any], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("user")
        db = data.get("db")
        if user is None or db is None:
            return await handler(event, data)

        # ادمین‌ها همیشه آزادند
        if data.get("is_admin"):
            return await handler(event, data)

        # اجازهٔ عبور دستورات پایه
        if isinstance(event, Message) and (event.text or "").split()[0] in ALLOWED_COMMANDS:
            return await handler(event, data)

        async with db.session_factory() as session:
            from app.services.settings_service import SettingsService

            settings = await SettingsService(session).get()
            if not settings.force_join_enabled:
                return await handler(event, data)

            from app.services.lock_service import LockService

            lock_service = LockService(session)
            channels = await lock_service.get_active_channels()

            not_joined: list = []
            if channels:
                bot: Bot = data["bot"]
                for ch in channels:
                    try:
                        member = await bot.get_chat_member(ch.chat_id, user.telegram_id)
                        if member.status in ("left", "kicked"):
                            not_joined.append(ch)
                    except TelegramAPIError as e:
                        # ربات ادمین کانال نیست یا کانال نامعتبر است → fail-open
                        logger.warning(f"get_chat_member خطا برای {ch.chat_id}: {e}")

            if not_joined:
                text = settings.lock_text or TEXTS["force_join"]
                await self._send_lock(event, text, force_join_keyboard(not_joined, "locks:check"))
                return None  # بلاک

            # چک قفل واکنش (فقط اگر عضویت کامل باشد)
            if settings.reaction_lock_enabled and not user.reacted_ok:
                rlock = await lock_service.get_active_reaction_lock()
                if rlock is not None:
                    await self._send_lock(event, TEXTS["reaction_lock"], None)
                    return None

        return await handler(event, data)

    async def _send_lock(self, event: Any, text: str, kb) -> None:
        """ارسال پیام قفل مناسب برای Message یا CallbackQuery."""
        if isinstance(event, CallbackQuery):
            try:
                await event.answer("🔒 ابتدا قفل‌ها را کامل کنید.", show_alert=True)
                await event.message.answer(text, reply_markup=kb)
            except Exception:  # noqa: BLE001
                pass
        elif isinstance(event, Message):
            await event.answer(text, reply_markup=kb)
