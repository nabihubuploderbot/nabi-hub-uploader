"""
handlers/reaction_lock.py — Reaction lock check handlers.

Handles the 'Check Reaction' button callback.
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
from keyboards.inline import CD, reaction_lock_check_keyboard

router = Router(name="reaction_lock")


@router.callback_query(F.data == CD.CHECK_REACTION)
async def check_reaction_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
    t: Callable[[str], str],
) -> None:
    """
    Re-check user reaction on required posts.

    Note: Telegram Bot API doesn't provide a direct way to check reactions
    programmatically. This handler provides a best-effort check and
    allows the user to proceed if they claim to have reacted.

    In production, consider using:
    1. A channel bot that monitors reactions
    2. UserBot (Telethon/Pyrogram) for reaction checking
    3. Manual admin verification
    """
    user_id = callback.from_user.id

    # Skip for admins
    if user_id == settings.MAIN_ADMIN_ID:
        await callback.answer(t("reaction_lock_passed"))
        return

    is_admin = await AdminService.is_admin(session, user_id)
    if is_admin:
        await callback.answer(t("reaction_lock_passed"))
        return

    # Get active reaction locks
    locks = await ChannelService.get_active_reaction_locks(session)
    if not locks:
        await UserService.set_reaction_passed(session, user_id, True)
        await callback.answer(t("reaction_lock_passed"))
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    # Since we can't programmatically verify reactions via Bot API,
    # we'll trust the user's self-declaration and mark as passed.
    # For production, integrate with a channel monitoring bot.

    await UserService.set_reaction_passed(session, user_id, True)
    await callback.answer(t("reaction_lock_passed"), show_alert=True)

    # Delete the reaction lock message
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Send welcome
    from services.setting_service import SettingService
    welcome = await SettingService.get(
        session, "welcome_message",
        default=t("welcome"),
    )
    await callback.message.answer(welcome, parse_mode="Markdown")

    logger.info(f"Reaction lock passed (self-declared): user_id={user_id}")
