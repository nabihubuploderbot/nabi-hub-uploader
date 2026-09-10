"""واکنش‌ها (قفل ری‌اکشن) + بررسی مجدد قفل‌ها / Reaction handler & re-check.

نکتهٔ مهم تلگرام: ربات نمی‌تواند ری‌اکشن‌ها را Poll کند؛ باید آپدیت
message_reaction را دریافت کنیم. در dispatcher این نوع آپدیت از طریق
resolve_used_update_types به‌صورت خودکار در allowed_updates ثبت می‌شود.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery, MessageReactionUpdated
from loguru import logger
from sqlalchemy import select

from app.core.db import Database
from app.locales.fa import TEXTS
from app.services.lock_service import LockService

router = Router(name="user_reactions")


@router.message_reaction()
async def on_reaction(event: MessageReactionUpdated, db: Database) -> None:
    """وقتی کاربر روی پست قفل‌شده واکنش می‌زند، دسترسی او در DB ثبت می‌شود."""
    if db is None:
        return

    async with db.session_factory() as session:
        lock_service = LockService(session)
        lock = await lock_service.get_active_reaction_lock()
        if lock is None or not lock.is_active:
            return
        if event.chat.id != lock.chat_id or event.message_id != lock.message_id:
            return

        # اگر ایموجی خاصی الزامی است چک می‌کنیم / Check required emoji
        if lock.required_emoji:
            new_emojis = [r.emoji for r in event.new_reaction if r.emoji]
            if lock.required_emoji not in new_emojis:
                return

        from app.models.user import User

        res = await session.execute(
            select(User).where(User.telegram_id == event.user.id)
        )
        user = res.scalar_one_or_none()
        if user:
            user.reacted_ok = True
            await session.commit()
            logger.info(f"👍 کاربر {event.user.id} روی پست قفل واکنش زد.")


@router.callback_query(F.data == "locks:check")
async def cb_check_locks(cb: CallbackQuery, db: Database) -> None:
    """دکمهٔ «بررسی مجدد» قفل‌ها / Re-check locks button."""
    async with db.session_factory() as session:
        from app.models.user import User

        res = await session.execute(
            select(User).where(User.telegram_id == cb.from_user.id)
        )
        user = res.scalar_one_or_none()
        if user is None:
            await cb.answer(TEXTS["not_found"], show_alert=True)
            return
        # ریست وضعیت تا Middleware دوباره چک زنده انجام دهد
        user.reacted_ok = False
        await session.commit()
    await cb.answer("🔄 در حال بررسی ... لطفاً دوباره تلاش کنید.", show_alert=False)
