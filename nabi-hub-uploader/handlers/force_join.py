"""
handlers/force_join.py — Force join check handlers.

Handles the 'Check Membership' button callback.
"""

from __future__ import annotations

from typing import Callable

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings
from services.admin_service import AdminService
from services.channel_service import ChannelService
from services.user_service import UserService
from utils.telegram import check_all_memberships
from keyboards.inline import CD, force_join_check_keyboard

router = Router(name="force_join")


@router.callback_query(F.data == CD.CHECK_JOIN)
async def check_membership_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
    t: Callable[[str], str],
) -> None:
    """Re-check user membership in all required channels."""
    user_id = callback.from_user.id

    # Skip for admins
    if user_id == settings.MAIN_ADMIN_ID:
        await callback.answer(t("force_join_passed"))
        return

    is_admin = await AdminService.is_admin(session, user_id)
    if is_admin:
        await callback.answer(t("force_join_passed"))
        return

    # Get active channels
    channels = await ChannelService.get_active_channels(session)
    if not channels:
        await UserService.set_force_join_passed(session, user_id, True)
        await callback.answer(t("force_join_passed"))
        # Try to delete the lock message
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    # Build channel info
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
        bot=bot,
        user_id=user_id,
        channels=channel_info,
    )

    if all_joined:
        await UserService.set_force_join_passed(session, user_id, True)
        await callback.answer(t("force_join_passed"), show_alert=True)

        # Try to delete the force join message
        try:
            await callback.message.delete()
        except Exception:
            pass

        # Send welcome message
        from services.setting_service import SettingService
        welcome = await SettingService.get(
            session, "welcome_message",
            default=t("welcome"),
        )
        await callback.message.answer(welcome, parse_mode="Markdown")

        logger.info(f"Force join passed: user_id={user_id}")
    else:
        # Show which channels are still missing
        not_joined = [r for r in results if not r["is_member"]]
        channels_for_kb = [
            {
                "display_name": r["channel_title"],
                "join_link": r["join_link"],
            }
            for r in not_joined
        ]

        await callback.answer(t("force_join_failed"), show_alert=True)

        # Update the message with current status
        try:
            status_text = t("force_join_msg") + "\n\n"
            for r in results:
                icon = "✅" if r["is_member"] else "❌"
                status_text += f"{icon} {r['channel_title']}\n"

            await callback.message.edit_text(
                status_text,
                reply_markup=force_join_check_keyboard(channels_for_kb),
            )
        except Exception:
            pass
