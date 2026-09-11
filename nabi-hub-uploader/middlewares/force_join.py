"""
middlewares/force_join.py — Force Join middleware.

Fixed: proper logging + handle new users + don't silently pass
"""

from __future__ import annotations

from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings
from services.admin_service import AdminService
from services.channel_service import ChannelService
from services.user_service import UserService
from utils.telegram import check_all_memberships
from keyboards.inline import force_join_check_keyboard


class ForceJoinMiddleware(BaseMiddleware):
    """
    Force Join middleware — blocks users who haven't joined required channels.
    """

    SKIP_CALLBACKS = {"check_join", "check_reaction"}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession = data.get("session")
        if not session:
            return await handler(event, data)

        # Extract user info
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            if event.data:
                for skip in self.SKIP_CALLBACKS:
                    if event.data.startswith(skip):
                        return await handler(event, data)

        if user_id is None:
            return await handler(event, data)

        # Skip for main admin
        if user_id == settings.MAIN_ADMIN_ID:
            return await handler(event, data)

        # Skip for other admins
        is_admin = await AdminService.is_admin(session, user_id)
        if is_admin:
            return await handler(event, data)

        # Get active force-join channels
        channels = await ChannelService.get_active_channels(session)
        if not channels:
            # هیچ کانال اجباری تنظیم نشده → ادامه بده
            return await handler(event, data)

        logger.info(f"🔒 Force join check for user {user_id}, {len(channels)} channels configured")

        # Check if user already passed (cached in DB)
        user = await UserService.get_by_id(session, user_id)
        if user and user.force_join_passed:
            logger.info(f"✅ User {user_id} already passed force join (cached)")
            return await handler(event, data)

        # ── بررسی عضویت ──

        channel_info = [
            {
                "channel_id": ch.channel_id,
                "channel_title": ch.display_name,
                "join_link": ch.join_link,
            }
            for ch in channels
        ]

        bot = data.get("bot")
        if not bot:
            logger.warning("⚠️ Bot not found in data!")
            return await handler(event, data)

        all_joined, results = await check_all_memberships(
            bot=bot, user_id=user_id, channels=channel_info,
        )

        # لاگ نتایج
        for r in results:
            logger.info(f"  Channel {r['channel_id']}: is_member={r['is_member']}, status={r['status']}")

        if all_joined:
            logger.info(f"✅ User {user_id} passed force join check")
            # ذخیره وضعیت — اول مطمئن بشیم کاربر وجود داره
            if not user:
                await UserService.get_or_create(
                    session=session, user_id=user_id,
                    username=event.from_user.username if event.from_user else None,
                    first_name=event.from_user.first_name if event.from_user else None,
                )
            await UserService.set_force_join_passed(session, user_id, True)
            return await handler(event, data)

        # ── کاربر عضو نشده → بلاک کن ──
        logger.info(f"❌ User {user_id} blocked by force join")

        not_joined = [r for r in results if not r["is_member"]]
        channels_for_keyboard = [
            {"display_name": r["channel_title"], "join_link": r["join_link"]}
            for r in not_joined
        ]

        from services.setting_service import SettingService
        msg_text = await SettingService.get(
            session, "force_join_message",
            default="⚠️ برای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید:",
        )

        if isinstance(event, Message):
            await event.answer(
                msg_text,
                reply_markup=force_join_check_keyboard(channels_for_keyboard),
            )
        elif isinstance(event, CallbackQuery):
            try:
                await event.message.edit_text(
                    msg_text,
                    reply_markup=force_join_check_keyboard(channels_for_keyboard),
                )
            except Exception:
                pass
            await event.answer()

        return  # Don't call the handler
