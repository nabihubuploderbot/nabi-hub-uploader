"""
handlers/start.py — /start command handler.

Handles:
- Initial bot start
- Deep link file access (/start FILE_TOKEN)
- Admin panel access
"""

from __future__ import annotations

from typing import Callable

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings
from services.user_service import UserService
from services.file_service import FileService
from services.admin_service import AdminService
from services.setting_service import SettingService
from utils.deep_link import extract_start_payload
from keyboards.inline import (
    admin_main_menu,
    get_file_keyboard,
    CD,
    panel_button,
)

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, t: Callable[[str], str], bot: Bot) -> None:
    """Handle /start command. Supports deep links: /start FILE_TOKEN"""
    user = message.from_user
    if not user:
        return

    await UserService.get_or_create(
        session=session, user_id=user.id, username=user.username,
        first_name=user.first_name, last_name=user.last_name,
        language_code=user.language_code or "fa", is_premium=user.is_premium or False,
    )

    # Check for deep link payload
    args = message.text.split()[1:] if message.text else []
    payload = extract_start_payload(args)

    if payload:
        await _handle_deep_link(message, session, payload, t, bot)
        return

    # Check if user is admin
    is_admin = await AdminService.is_admin(session, user.id)

    if is_admin:
        await message.answer(t("welcome_admin"), reply_markup=admin_main_menu(), parse_mode="Markdown")
    else:
        bot_enabled = await SettingService.get_bool(session, "bot_enabled", default=True)
        if not bot_enabled:
            await message.answer("🔴 ربات در حال حاضر غیرفعال است.", reply_markup=panel_button())
            return
        welcome_text = await SettingService.get(session, "welcome_message", default=t("welcome"))
        await message.answer(welcome_text, parse_mode="Markdown")


async def _handle_deep_link(message: Message, session: AsyncSession, token: str, t: Callable[[str], str], bot: Bot) -> None:
    """Handle deep link file access."""
    file_record = await FileService.get_by_token(session, token)
    if not file_record:
        await message.answer(t("file_not_found"), reply_markup=panel_button())
        return

    bot_enabled = await SettingService.get_bool(session, "bot_enabled", default=True)
    if not bot_enabled:
        await message.answer("🔴 ربات در حال حاضر غیرفعال است.", reply_markup=panel_button())
        return

    delay = await SettingService.get_int(session, "delay_before_send", default=0)
    if delay > 0:
        await message.answer(f"⏱ فایل پس از {delay} ثانیه ارسال خواهد شد...")
        import asyncio
        await asyncio.sleep(delay)

    await _send_file(message, file_record, t, session)


async def _send_file(message: Message, file_record, t: Callable[[str], str], session: AsyncSession) -> None:
    """Send a file to the user based on its type."""
    caption = file_record.caption or ""
    reply_markup = get_file_keyboard(file_record.deep_link_token)

    try:
        file_type = file_record.file_type
        file_id = file_record.file_id

        if file_type == "document":
            await message.answer_document(document=file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
        elif file_type == "photo":
            await message.answer_photo(photo=file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
        elif file_type == "video":
            await message.answer_video(video=file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
        elif file_type == "audio":
            await message.answer_audio(audio=file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
        elif file_type == "voice":
            await message.answer_voice(voice=file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
        elif file_type == "video_note":
            await message.answer_video_note(video_note=file_id, reply_markup=reply_markup)
        elif file_type == "animation":
            await message.answer_animation(animation=file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await message.answer_document(document=file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)

        await FileService.increment_download(session, file_record.id)
        await UserService.increment_downloads(session, message.from_user.id)
        logger.info(f"File sent: token={file_record.deep_link_token} type={file_type} user={message.from_user.id}")

    except Exception as e:
        logger.error(f"Failed to send file {file_record.id}: {e}")
        await message.answer(t("error_occurred"), reply_markup=panel_button())


@router.message(Command("help"))
async def cmd_help(message: Message, t: Callable[[str], str]) -> None:
    """Handle /help command."""
    await message.answer(
        "📖 **راهنمای ربات Nabi Hub | Uploader**\n\n"
        "• از لینک‌های عمیق برای دریافت فایل استفاده کنید\n"
        "• `/start` — شروع ربات\n"
        "• `/help` — نمایش راهنما",
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith(f"{CD.GET_FILE}:"))
async def cb_get_file(callback: CallbackQuery, session: AsyncSession, t: Callable[[str], str]) -> None:
    """Re-send the file when the user presses the get-file button."""
    token = callback.data.split(":", 1)[1]
    file_record = await FileService.get_by_token(session, token)
    if not file_record:
        await callback.answer(t("file_not_found"), show_alert=True)
        return
    await _send_file(callback.message, file_record, t, session)
    await callback.answer()
