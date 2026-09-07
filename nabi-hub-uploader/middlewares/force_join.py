"""
middlewares/force_join.py — Force Join middleware.

Checks if the user has joined all required channels before proceeding.
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
    Middleware to enforce channel membership before using the bot.

    Skips the check for:
    - Admin users
    - The /start command (so users can see what channels to join)
    - Callback queries with CHECK_JOIN callback data (to re-check)
    """

    # Handlers/callbacks that should skip the force join check
    SKIP_COMMANDS = {"start", "help", "admin"}
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
            # Skip certain commands
            if event.text and event.text.startswith("/"):
                command = event.text.split()[0].split("@")[0][1:]
                if command in self.SKIP_COMMANDS:
                    return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            # Skip certain callbacks
            if event.data:
                for skip in self.SKIP_CALLBACKS:
                    if event.data.startswith(skip):
                        return await handler(event, data)

        if user_id is None:
            return await handler(event, data)

        # Skip for admins
        is_admin = await AdminService.is_admin(session, user_id)
        if is_admin or user_id == settings.MAIN_ADMIN_ID:
            return await handler(event, data)

        # Get active force-join channels
        channels = await ChannelService.get_active_channels(session)
        if not channels:
            return await handler(event, data)

        # Check if user already passed (cached)
        user = await UserService.get_by_id(session, user_id)
        if user and user.force_join_passed:
            return await handler(event, data)

        # Build channel info for checking
        channel_info = [
            {
                "channel_id": ch.channel_id,
                "channel_title": ch.display_name,
                "join_link": ch.join_link,
            }
            for ch in channels
        ]

        # Check membership
        all_joined, results = await check_all_memberships(
            bot=data["bot"],
            user_id=user_id,
            channels=channel_info,
        )

        if all_joined:
            await UserService.set_force_join_passed(session, user_id, True)
            return await handler(event, data)

        # User hasn't joined all channels — show the force join message
        not_joined = [r for r in results if not r["is_member"]]
        channels_for_keyboard = [
            {
                "display_name": r["channel_title"],
                "join_link": r["join_link"],
            }
            for r in not_joined
        ]

        # Get custom message
        from services.setting_service import SettingService
        msg_text = await SettingService.get(
            session,
            "force_join_message",
            default="⚠️ برای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید:",
        )

        if isinstance(event, Message):
            await event.answer(
                msg_text,
                reply_markup=force_join_check_keyboard(channels_for_keyboard),
            )
        elif isinstance(event, CallbackQuery):
            await event.message.edit_text(
                msg_text,
                reply_markup=force_join_check_keyboard(channels_for_keyboard),
            )
            await event.answer()

        return  # Don't call the handler
