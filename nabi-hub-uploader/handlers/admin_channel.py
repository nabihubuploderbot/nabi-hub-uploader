"""
admin_channel.py — ارسال به کانال + مدیریت گروه

Handles:
- settings_channel: ارسال پیام به کانال مشخص
- settings_group: تنظیم گروه و ارسال به گروه
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
    back_button,
)
from keyboards.reply import admin_reply_menu, remove_keyboard

router = Router(name="admin_channel")


# ── FSM States ──────────────────────────────────────

class ChannelStates(StatesGroup):
    """FSM states for channel operations."""
    waiting_channel_id = State()         # تنظیم کانال مقصد
    waiting_channel_message = State()    # نوشتن پیام برای کانال
    waiting_channel_media = State()      # ارسال رسانه به کانال
    waiting_group_id = State()           # تنظیم گروه
    waiting_group_message = State()      # نوشتن پیام برای گروه


# ═══════════════════════════════════════════════════════
# 📤 ارسال به کانال
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.SETTINGS_CHANNEL)
async def show_channel_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """نمایش تنظیمات ارسال به کانال."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    channel_id = await SettingService.get(session, "forward_channel_id", "")

    if channel_id:
        status = f"✅ تنظیم شده: `{channel_id}`"
    else:
        status = "❌ تنظیم نشده"

    text = (
        "📤 **ارسال به کانال**\n\n"
        f"کانال مقصد: {status}\n\n"
        "از دکمه‌های زیر استفاده کنید:"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📝 ارسال متن به کانال",
            callback_data="ch_send_text",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🖼 ارسال رسانه به کانال",
            callback_data="ch_send_media",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⚙️ تنظیم کانال مقصد",
            callback_data="ch_set_target",
        ),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADMIN_SETTINGS),
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ── تنظیم کانال مقصد ───────────────────────────────


@router.callback_query(F.data == "ch_set_target")
async def start_set_channel_target(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """شروع تنظیم کانال مقصد."""
    if not is_admin:
        return

    await state.set_state(ChannelStates.waiting_channel_id)
    await callback.message.edit_text(
        "⚙️ **تنظیم کانال مقصد**\n\n"
        "لطفاً آیدی عددی کانال را وارد کنید:\n\n"
        "مثال: `-1001234567890`\n\n"
        "یا نام کاربری: `@channel_username`",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ChannelStates.waiting_channel_id)
async def process_channel_target(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """پردازش آیدی کانال مقصد."""
    text = message.text.strip()

    # تبدیل به آیدی عددی
    channel_id = None
    if text.startswith("-") or text.isdigit():
        try:
            channel_id = int(text)
        except ValueError:
            pass

    if not channel_id:
        # تلاش برای resolve کردن یوزرنیم
        username = text.lstrip("@")
        try:
            chat = await bot.get_chat(username)
            channel_id = chat.id
        except Exception:
            await message.answer(
                "⚠️ کانال یافت نشد. لطفاً آیدی عددی صحیح وارد کنید.\n"
                "مثال: `-1001234567890`"
            )
            return

    # ذخیره در دیتابیس
    await SettingService.set(session, "forward_channel_id", str(channel_id))

    await state.clear()
    await message.answer(
        f"✅ **کانال مقصد تنظیم شد:**\n\n"
        f"🆔 آیدی: `{channel_id}`\n\n"
        "حالا می‌توانید از بخش «ارسال به کانال» پیام ارسال کنید.",
        parse_mode="Markdown",
        reply_markup=admin_reply_menu(),
    )


# ── ارسال متن به کانال ────────────────────────────


@router.callback_query(F.data == "ch_send_text")
async def start_send_to_channel(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """شروع ارسال متن به کانال."""
    if not is_admin:
        return

    channel_id = await SettingService.get(session, "forward_channel_id", "")
    if not channel_id:
        await callback.answer(
            "⚠️ ابتدا کانال مقصد را تنظیم کنید!",
            show_alert=True,
        )
        return

    await state.set_state(ChannelStates.waiting_channel_message)
    await callback.message.edit_text(
        f"📝 **ارسال متن به کانال** `{channel_id}`\n\n"
        "لطفاً پیام مورد نظر را بنویسید:\n\n"
        "از HTML می‌توانید استفاده کنید.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ChannelStates.waiting_channel_message)
async def process_send_to_channel(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """ارسال پیام متنی به کانال."""
    channel_id_str = await SettingService.get(session, "forward_channel_id", "")

    if not channel_id_str:
        await message.answer("⚠️ کانال مقصد تنظیم نشده!")
        await state.clear()
        return

    channel_id = int(channel_id_str)
    text = message.html_text or message.text

    try:
        sent = await bot.send_message(
            chat_id=channel_id,
            text=text,
            parse_mode="HTML",
        )
        await state.clear()
        await message.answer(
            f"✅ **پیام با موفقیت به کانال ارسال شد!**\n\n"
            f"📨 آیدی پیام: `{sent.message_id}`",
            parse_mode="Markdown",
            reply_markup=admin_reply_menu(),
        )
        logger.info(f"Message sent to channel {channel_id} by admin {message.from_user.id}")
    except Exception as e:
        await message.answer(
            f"⚠️ **خطا در ارسال پیام:**\n\n`{str(e)}`\n\n"
            "مطمئن شوید:\n"
            "1. ربات ادمین کانال است\n"
            "2. آیدی کانال صحیح است",
            parse_mode="Markdown",
        )
        logger.error(f"Failed to send to channel {channel_id}: {e}")


# ── ارسال رسانه به کانال ──────────────────────────


@router.callback_query(F.data == "ch_send_media")
async def start_send_media_to_channel(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """شروع ارسال رسانه به کانال."""
    if not is_admin:
        return

    channel_id = await SettingService.get(session, "forward_channel_id", "")
    if not channel_id:
        await callback.answer(
            "⚠️ ابتدا کانال مقصد را تنظیم کنید!",
            show_alert=True,
        )
        return

    await state.set_state(ChannelStates.waiting_channel_media)
    await callback.message.edit_text(
        f"🖼 **ارسال رسانه به کانال** `{channel_id}`\n\n"
        "لطفاً فایل رسانه‌ای (عکس، ویدیو، سند) را ارسال کنید.\n"
        "کپشن اختیاری است.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ChannelStates.waiting_channel_media, F.content_type.in_({
    "photo", "video", "document", "audio", "voice", "animation",
}))
async def process_send_media_to_channel(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """ارسال رسانه به کانال."""
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
                f"✅ **رسانه با موفقیت به کانال ارسال شد!**\n\n"
                f"📨 آیدی پیام: `{sent.message_id}`",
                parse_mode="Markdown",
                reply_markup=admin_reply_menu(),
            )
        logger.info(f"Media sent to channel {channel_id} by admin {message.from_user.id}")
    except Exception as e:
        await message.answer(
            f"⚠️ **خطا در ارسال:**\n\n`{str(e)}`",
            parse_mode="Markdown",
        )
        logger.error(f"Failed to send media to channel {channel_id}: {e}")


# ═══════════════════════════════════════════════════════
# 💬 گروه
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.SETTINGS_GROUP)
async def show_group_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """نمایش تنظیمات گروه."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    group_id = await SettingService.get(session, "group_id", "")

    if group_id:
        status = f"✅ تنظیم شده: `{group_id}`"
    else:
        status = "❌ تنظیم نشده"

    text = (
        "💬 **تنظیمات گروه**\n\n"
        f"گروه فعلی: {status}\n\n"
        "از دکمه‌های زیر استفاده کنید:"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⚙️ تنظیم گروه",
            callback_data="grp_set_target",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📝 ارسال پیام به گروه",
            callback_data="grp_send_text",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 حذف گروه",
            callback_data="grp_remove",
        ),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADMIN_SETTINGS),
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "grp_set_target")
async def start_set_group(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """شروع تنظیم گروه."""
    if not is_admin:
        return

    await state.set_state(ChannelStates.waiting_group_id)
    await callback.message.edit_text(
        "⚙️ **تنظیم گروه**\n\n"
        "لطفاً آیدی عددی گروه را وارد کنید:\n\n"
        "مثال: `-1001234567890`\n\n"
        "⚠️ **نکته:** ربات باید عضو گروه باشد.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ChannelStates.waiting_group_id)
async def process_group_id(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """پردازش آیدی گروه."""
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
            await message.answer("⚠️ گروه یافت نشد. آیدی عددی صحیح وارد کنید.")
            return

    # تست ارسال به گروه
    try:
        test_msg = await bot.send_message(
            chat_id=group_id,
            text="✅ اتصال ربات به گروه با موفقیت انجام شد.\n\nاین پیام آزمایشی است.",
        )
        # حذف پیام آزمایشی
        try:
            await bot.delete_message(group_id, test_msg.message_id)
        except Exception:
            pass
    except Exception as e:
        await message.answer(
            f"⚠️ **خطا در اتصال به گروه:**\n\n`{str(e)}`\n\n"
            "مطمئن شوید ربات عضو گروه است و دسترسی ارسال پیام دارد.",
            parse_mode="Markdown",
        )
        return

    await SettingService.set(session, "group_id", str(group_id))
    await state.clear()
    await message.answer(
        f"✅ **گروه تنظیم شد:**\n\n"
        f"🆔 آیدی: `{group_id}`\n\n"
        "اتصال به گروه با موفقیت تست شد.",
        parse_mode="Markdown",
        reply_markup=admin_reply_menu(),
    )


@router.callback_query(F.data == "grp_send_text")
async def start_send_to_group(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """شروع ارسال پیام به گروه."""
    if not is_admin:
        return

    group_id = await SettingService.get(session, "group_id", "")
    if not group_id:
        await callback.answer(
            "⚠️ ابتدا گروه را تنظیم کنید!",
            show_alert=True,
        )
        return

    await state.set_state(ChannelStates.waiting_group_message)
    await callback.message.edit_text(
        f"📝 **ارسال پیام به گروه** `{group_id}`\n\n"
        "لطفاً پیام مورد نظر را بنویسید:",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ChannelStates.waiting_group_message)
async def process_send_to_group(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """ارسال پیام به گروه."""
    group_id_str = await SettingService.get(session, "group_id", "")
    group_id = int(group_id_str)
    text = message.html_text or message.text

    try:
        await bot.send_message(
            chat_id=group_id,
            text=text,
            parse_mode="HTML",
        )
        await state.clear()
        await message.answer(
            "✅ **پیام با موفقیت به گروه ارسال شد!**",
            parse_mode="Markdown",
            reply_markup=admin_reply_menu(),
        )
    except Exception as e:
        await message.answer(
            f"⚠️ **خطا در ارسال:**\n\n`{str(e)}`",
            parse_mode="Markdown",
        )


@router.callback_query(F.data == "grp_remove")
async def remove_group(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """حذف گروه."""
    if not is_admin:
        return

    await SettingService.delete(session, "group_id")
    await callback.answer("✅ گروه حذف شد.", show_alert=True)

    # Refresh
    await show_group_settings(callback, session, is_admin, lambda k: k)
