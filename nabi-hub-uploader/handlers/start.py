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
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings
from services.user_service import UserService
from services.file_service import FileService
from services.admin_service import AdminService
from services.setting_service import SettingService
from services.channel_service import ChannelService
from utils.deep_link import extract_start_payload
from utils.telegram import (
    get_file_type,
    get_file_id_and_unique_id,
    get_file_size,
    get_file_name,
    get_mime_type,
)
from keyboards.inline import (
    admin_main_menu,
    force_join_check_keyboard,
    get_file_keyboard,
    CD,
)

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    session: AsyncSession,
    t: Callable[[str], str],
    bot: Bot,
) -> None:
    """
    Handle /start command.

    Supports deep links: /start FILE_TOKEN
    """
    user = message.from_user
    if not user:
        return

    # Register/update user
    await UserService.get_or_create(
        session=session,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code or "fa",
        is_premium=user.is_premium or False,
    )

    # Check for deep link payload
    args = message.text.split()[1:] if message.text else []
    payload = extract_start_payload(args)

    if payload:
        # Deep link: try to send the file
        await _handle_deep_link(message, session, payload, t, bot)
        return

    # Check if user is admin
    is_admin = await AdminService.is_admin(session, user.id)

    if is_admin:
        # Show admin panel
        await message.answer(
            t("welcome_admin"),
            reply_markup=admin_main_menu(),
            parse_mode="Markdown",
        )
    else:
        # Show normal welcome
        bot_enabled = await SettingService.get_bool(
            session, "bot_enabled", default=True
        )
        if not bot_enabled:
            await message.answer(
                "🔴 ربات در حال حاضر غیرفعال است. لطفاً بعداً تلاش کنید."
            )
            return

        welcome_text = await SettingService.get(
            session, "welcome_message", default=t("welcome")
        )

        await message.answer(
            welcome_text,
            parse_mode="Markdown",
        )


async def _handle_deep_link(
    message: Message,
    session: AsyncSession,
    token: str,
    t: Callable[[str], str],
    bot: Bot,
) -> None:
    """Handle deep link file access."""
    # Find file by token
    file_record = await FileService.get_by_token(session, token)

    if not file_record:
        await message.answer(t("file_not_found"))
        return

    # Check if bot is enabled
    bot_enabled = await SettingService.get_bool(
        session, "bot_enabled", default=True
    )
    if not bot_enabled:
        await message.answer("🔴 ربات در حال حاضر غیرفعال است.")
        return

    # Get delay setting
    delay = await SettingService.get_int(session, "delay_before_send", default=0)

    if delay > 0:
        await message.answer(f"⏱ فایل پس از {delay} ثانیه ارسال خواهد شد...")
        import asyncio
        await asyncio.sleep(delay)

    # Send the file
    await _send_file(message, file_record, t, session)


async def _send_file(
    message: Message,
    file_record,
    t: Callable[[str], str],
    session: AsyncSession,
) -> None:
    """Send a file to the user based on its type."""
    caption = file_record.caption or ""

    # Get custom button settings
    from services.setting_service import SettingService
    show_buttons = await SettingService.get_bool(
        session, "show_buttons", default=True
    )

    extra_buttons = None
    if show_buttons:
        button_text = await SettingService.get(session, "button_text")
        button_url = await SettingService.get(session, "button_url")
        if button_text and button_url:
            from aiogram.types import InlineKeyboardButton
            extra_buttons = [
                InlineKeyboardButton(text=button_text, url=button_url)
            ]

    reply_markup = get_file_keyboard(file_record.deep_link_token)
    # Note: In production, add extra buttons to the keyboard

    try:
        file_type = file_record.file_type
        file_id = file_record.file_id

        if file_type == "document":
            await message.answer_document(
                document=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        elif file_type == "photo":
            await message.answer_photo(
                photo=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        elif file_type == "video":
            await message.answer_video(
                video=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        elif file_type == "audio":
            await message.answer_audio(
                audio=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        elif file_type == "voice":
            await message.answer_voice(
                voice=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        elif file_type == "video_note":
            await message.answer_video_note(
                video_note=file_id,
                reply_markup=reply_markup,
            )
        elif file_type == "animation":
            await message.answer_animation(
                animation=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        else:
            # Fallback: send as document
            await message.answer_document(
                document=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )

        # Update counters
        await FileService.increment_download(session, file_record.id)
        await UserService.increment_downloads(session, message.from_user.id)

        logger.info(
            f"File sent: token={file_record.deep_link_token} "
            f"type={file_type} user={message.from_user.id}"
        )

    except Exception as e:
        logger.error(f"Failed to send file {file_record.id}: {e}")
        await message.answer(t("error_occurred"))


@router.message(Command("help"))
async def cmd_help(message: Message, t: Callable[[str], str]) -> None:
    """Handle /help command."""
    await message.answer(
        "📖 **راهنمای ربات Nabi Hub | Uploader**\n\n"
        "• از لینک‌های عمیق برای دریافت فایل استفاده کنید\n"
        "• `/start` — شروع ربات\n"
        "• `/help` — نمایش راهنما\n\n"
        "برای پشتیبانی با ادمین تماس بگیرید.",
        parse_mode="Markdown",
    )
