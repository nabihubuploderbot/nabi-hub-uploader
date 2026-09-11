"""
admin_channel.py — ارسال به کانال + مدیریت گروه

همه پیام‌ها دکمه اینلاین دارن ✅
"""

from __future__ import annotations

from typing import Callable

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from services.setting_service import SettingService
from keyboards.inline import (
    CD,
    panel_button,
    settings_button,
    back_button,
    cancel_panel_button,
)

router = Router(name="admin_channel")


class ChannelStates(StatesGroup):
    waiting_channel_id = State()
    waiting_channel_message = State()
    waiting_channel_media = State()
    waiting_group_id = State()
    waiting_group_message = State()


# ═══════════════════════════════════════════════════════
# 📤 ارسال به کانال
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.SETTINGS_CHANNEL)
async def show_channel_settings(callback: CallbackQuery, session: AsyncSession, is_admin: bool, t: Callable[[str], str]) -> None:
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return
    channel_id = await SettingService.get(session, "forward_channel_id", "")
    status = f"✅ `{channel_id}`" if channel_id else "❌ تنظیم نشده"
    text = f"📤 **ارسال به کانال**\n\nکانال مقصد: {status}"
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 ارسال متن به کانال", callback_data="ch_send_text"))
    builder.row(InlineKeyboardButton(text="🖼 ارسال رسانه به کانال", callback_data="ch_send_media"))
    builder.row(InlineKeyboardButton(text="⚙️ تنظیم کانال مقصد", callback_data="ch_set_target"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADMIN_SETTINGS))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "ch_set_target")
async def start_set_channel_target(callback: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    if not is_admin:
        return
    await state.set_state(ChannelStates.waiting_channel_id)
    await callback.message.edit_text(
        "⚙️ **تنظیم کانال مقصد**\n\nآیدی عددی کانال را وارد کنید:\n\nمثال: `-1001234567890`",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ChannelStates.waiting_channel_id)
async def process_channel_target(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    text = message.text.strip()
    channel_id = None
    if text.startswith("-") or text.isdigit():
        try:
            channel_id = int(text)
        except ValueError:
            pass
    if not channel_id:
        username = text.lstrip("@")
        try:
            chat = await bot.get_chat(username)
            channel_id = chat.id
        except Exception:
            await message.answer(
                "⚠️ **کانال یافت نشد!**\n\nآیدی عددی صحیح وارد کنید.",
                parse_mode="Markdown",
                reply_markup=cancel_panel_button(),
            )
            return
    await SettingService.set(session, "forward_channel_id", str(channel_id))
    await state.clear()
    await message.answer(
        f"✅ **کانال مقصد تنظیم شد:**\n\n🆔 آیدی: `{channel_id}`",
        parse_mode="Markdown",
        reply_markup=settings_button(),
    )


@router.callback_query(F.data == "ch_send_text")
async def start_send_to_channel(callback: CallbackQuery, state: FSMContext, session: AsyncSession, is_admin: bool) -> None:
    if not is_admin:
        return
    channel_id = await SettingService.get(session, "forward_channel_id", "")
    if not channel_id:
        await callback.answer("⚠️ ابتدا کانال مقصد را تنظیم کنید!", show_alert=True)
        return
    await state.set_state(ChannelStates.waiting_channel_message)
    await callback.message.edit_text(
        f"📝 **ارسال متن به کانال** `{channel_id}`\n\nپیام مورد نظر را بنویسید:",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ChannelStates.waiting_channel_message)
async def process_send_to_channel(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    channel_id_str = await SettingService.get(session, "forward_channel_id", "")
    if not channel_id_str:
        await message.answer("⚠️ کانال مقصد تنظیم نشده!", reply_markup=settings_button())
        await state.clear()
        return
    channel_id = int(channel_id_str)
    text = message.html_text or message.text
    try:
        sent = await bot.send_message(chat_id=channel_id, text=text, parse_mode="HTML")
        await state.clear()
        await message.answer(
            f"✅ **پیام به کانال ارسال شد!**\n\n📨 آیدی پیام: `{sent.message_id}`",
            parse_mode="Markdown",
            reply_markup=settings_button(),
        )
        logger.info(f"Message sent to channel {channel_id} by admin {message.from_user.id}")
    except Exception as e:
        await message.answer(
            f"⚠️ **خطا در ارسال:**\n\n`{str(e)}`\n\nربات ادمین کانال است؟",
            parse_mode="Markdown",
            reply_markup=settings_button(),
        )
        logger.error(f"Failed to send to channel {channel_id}: {e}")


@router.callback_query(F.data == "ch_send_media")
async def start_send_media_to_channel(callback: CallbackQuery, state: FSMContext, session: AsyncSession, is_admin: bool) -> None:
    if not is_admin:
        return
    channel_id = await SettingService.get(session, "forward_channel_id", "")
    if not channel_id:
        await callback.answer("⚠️ ابتدا کانال مقصد را تنظیم کنید!", show_alert=True)
        return
    await state.set_state(ChannelStates.waiting_channel_media)
    await callback.message.edit_text(
        f"🖼 **ارسال رسانه به کانال** `{channel_id}`\n\nفایل رسانه‌ای را ارسال کنید:",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ChannelStates.waiting_channel_media, F.content_type.in_({"photo", "video", "document", "audio", "voice", "animation"}))
async def process_send_media_to_channel(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    channel_id_str = await SettingService.get(session, "forward_channel_id", "")
    channel_id = int(channel_id_str)
    caption = message.caption or ""
    try:
        sent = None
        if message.photo:
            sent = await bot.send_photo(channel_id, message.photo[-1].file_id, caption=caption)
        elif message.video:
            sent = await bot.send_video(channel_id, message.video.file_id, caption=caption)
        elif message.document:
            sent = await bot.send_document(channel_id, message.document.file_id, caption=caption)
        elif message.audio:
            sent = await bot.send_audio(channel_id, message.audio.file_id, caption=caption)
        elif message.voice:
            sent = await bot.send_voice(channel_id, message.voice.file_id, caption=caption)
        elif message.animation:
            sent = await bot.send_animation(channel_id, message.animation.file_id, caption=caption)
        await state.clear()
        if sent:
            await message.answer(
                f"✅ **رسانه به کانال ارسال شد!**\n\n📨 آیدی: `{sent.message_id}`",
                parse_mode="Markdown",
                reply_markup=settings_button(),
            )
    except Exception as e:
        await message.answer(
            f"⚠️ **خطا:**\n\n`{str(e)}`",
            parse_mode="Markdown",
            reply_markup=settings_button(),
        )


# ═══════════════════════════════════════════════════════
# 💬 گروه
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.SETTINGS_GROUP)
async def show_group_settings(callback: CallbackQuery, session: AsyncSession, is_admin: bool, t: Callable[[str], str]) -> None:
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return
    group_id = await SettingService.get(session, "group_id", "")
    status = f"✅ `{group_id}`" if group_id else "❌ تنظیم نشده"
    text = f"💬 **تنظیمات گروه**\n\nگروه فعلی: {status}"
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⚙️ تنظیم گروه", callback_data="grp_set_target"))
    builder.row(InlineKeyboardButton(text="📝 ارسال پیام به گروه", callback_data="grp_send_text"))
    builder.row(InlineKeyboardButton(text="🗑 حذف گروه", callback_data="grp_remove"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADMIN_SETTINGS))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "grp_set_target")
async def start_set_group(callback: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    if not is_admin:
        return
    await state.set_state(ChannelStates.waiting_group_id)
    await callback.message.edit_text(
        "⚙️ **تنظیم گروه**\n\nآیدی عددی گروه را وارد کنید:\n\nمثال: `-1001234567890`\n\n⚠️ ربات باید عضو گروه باشد.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ChannelStates.waiting_group_id)
async def process_group_id(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    text = message.text.strip()
    group_id = None
    if text.startswith("-") or text.lstrip("-").isdigit():
        try:
            group_id = int(text)
        except ValueError:
            pass
    if not group_id:
        username = text.lstrip("@")
        try:
            chat = await bot.get_chat(username)
            group_id = chat.id
        except Exception:
            await message.answer(
                "⚠️ **گروه یافت نشد!**\n\nآیدی عددی صحیح وارد کنید.",
                parse_mode="Markdown",
                reply_markup=cancel_panel_button(),
            )
            return
    try:
        test_msg = await bot.send_message(chat_id=group_id, text="✅ اتصال موفق!")
        try:
            await bot.delete_message(group_id, test_msg.message_id)
        except Exception:
            pass
    except Exception as e:
        await message.answer(
            f"⚠️ **خطا در اتصال:**\n\n`{str(e)}`\n\nربات عضو گروه است؟",
            parse_mode="Markdown",
            reply_markup=cancel_panel_button(),
        )
        return
    await SettingService.set(session, "group_id", str(group_id))
    await state.clear()
    await message.answer(
        f"✅ **گروه تنظیم شد!**\n\n🆔 آیدی: `{group_id}`",
        parse_mode="Markdown",
        reply_markup=settings_button(),
    )


@router.callback_query(F.data == "grp_send_text")
async def start_send_to_group(callback: CallbackQuery, state: FSMContext, session: AsyncSession, is_admin: bool) -> None:
    if not is_admin:
        return
    group_id = await SettingService.get(session, "group_id", "")
    if not group_id:
        await callback.answer("⚠️ ابتدا گروه را تنظیم کنید!", show_alert=True)
        return
    await state.set_state(ChannelStates.waiting_group_message)
    await callback.message.edit_text(
        f"📝 **ارسال پیام به گروه** `{group_id}`\n\nپیام مورد نظر را بنویسید:",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ChannelStates.waiting_group_message)
async def process_send_to_group(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    group_id_str = await SettingService.get(session, "group_id", "")
    group_id = int(group_id_str)
    text = message.html_text or message.text
    try:
        await bot.send_message(chat_id=group_id, text=text, parse_mode="HTML")
        await state.clear()
        await message.answer("✅ **پیام به گروه ارسال شد!**", parse_mode="Markdown", reply_markup=settings_button())
    except Exception as e:
        await message.answer(f"⚠️ **خطا:**\n\n`{str(e)}`", parse_mode="Markdown", reply_markup=settings_button())


@router.callback_query(F.data == "grp_remove")
async def remove_group(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    if not is_admin:
        return
    await SettingService.delete(session, "group_id")
    await callback.message.edit_text(
        "✅ **گروه حذف شد.**",
        parse_mode="Markdown",
        reply_markup=settings_button(),
    )
    await callback.answer()
