"""
admin_panel.py — ناوبری اصلی پنل مدیریت

فقط هندلرهای ناوبری اصلی پنل اینجا هستند.
مدیریت ادمین → admin_manage.py
ارسال به کانال و گروه → admin_channel.py
"""

from __future__ import annotations

from typing import Callable

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from services.user_service import UserService
from services.file_service import FileService
from services.admin_service import AdminService
from services.channel_service import ChannelService
from services.setting_service import SettingService
from keyboards.inline import (
    CD,
    admin_main_menu,
    admin_settings_menu,
    admin_broadcast_menu,
    admin_stats_keyboard,
    admin_file_management,
    admin_user_management,
    force_join_menu,
    reaction_lock_menu,
    on_off_keyboard,
    back_button,
)

router = Router(name="admin_panel")


# ── FSM States ──────────────────────────────────────
class PanelStates(StatesGroup):
    """FSM states for panel inline operations."""
    waiting_channel_id_fj = State()
    waiting_reaction_channel = State()
    waiting_reaction_message = State()


# ═══════════════════════════════════════════════════════
# ورود به پنل
# ═══════════════════════════════════════════════════════


@router.message(Command("admin"))
@router.message(F.text == "📋 پنل مدیریت")
async def open_admin_panel(
    message: Message,
    session: AsyncSession,
    t: Callable[[str], str],
    is_admin: bool,
) -> None:
    """باز کردن پنل مدیریت."""
    if not is_admin:
        return

    await message.answer(
        t("welcome_admin"),
        reply_markup=admin_main_menu(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == CD.ADMIN_PANEL)
async def show_admin_panel(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """نمایش پنل اصلی."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        t("welcome_admin"),
        reply_markup=admin_main_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# منوی تنظیمات
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADMIN_SETTINGS)
async def show_settings(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """نمایش منوی تنظیمات."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        "⚙️ **تنظیمات کلی**\n\nاز منوی زیر بخش مورد نظر را انتخاب کنید:",
        reply_markup=admin_settings_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# آمار
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADMIN_STATS)
async def show_stats(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """نمایش آمار ربات."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    users_count = await UserService.count_users(session)
    files_count = await FileService.count_files(session)
    admins_count = await AdminService.count_admins(session)
    downloads_count = await FileService.count_total_downloads(session)
    channels_count = await ChannelService.count_channels(session)
    banned_count = await UserService.count_banned(session)

    stats_text = (
        f"📊 **آمار ربات Nabi Hub | Uploader**\n\n"
        f"👥 کاربران کل: **{users_count:,}**\n"
        f"🚫 کاربران بن‌شده: **{banned_count:,}**\n"
        f"📁 فایل‌ها: **{files_count:,}**\n"
        f"📥 دانلودها: **{downloads_count:,}**\n"
        f"👑 ادمین‌ها: **{admins_count}**\n"
        f"📢 کانال‌های قفل: **{channels_count}**\n"
    )

    await callback.message.edit_text(
        stats_text,
        reply_markup=admin_stats_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer("📊 آمار بروزرسانی شد")


# ═══════════════════════════════════════════════════════
# کپشن و متون
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADMIN_CAPTION)
async def show_caption_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """نمایش تنظیمات کپشن."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    current_caption = await SettingService.get(session, "file_caption", "")
    album_caption = await SettingService.get(session, "album_caption", "")

    text = (
        "📝 **تنظیم کپشن**\n\n"
        f"📄 کپشن فعلی فایل:\n`{current_caption or '(تنظیم نشده)'}\n`\n"
        f"📦 کپشن فعلی آلبوم:\n`{album_caption or '(تنظیم نشده)'}\n`\n\n"
        "برای تغییر، کپشن جدید را ارسال کنید.\n"
        "از /clearcaption برای حذف کپشن استفاده کنید."
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADMIN_PANEL),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_TEXTS)
async def show_texts_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """نمایش تنظیم متون."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    welcome = await SettingService.get(session, "welcome_message", "") or ""
    fj_msg = await SettingService.get(session, "force_join_message", "") or ""
    rl_msg = await SettingService.get(session, "reaction_lock_message", "") or ""

    text = (
        "📝 **تنظیم متون ربات**\n\n"
        f"👋 پیام خوش‌آمدگویی:\n{welcome[:200]}{'...' if len(welcome) > 200 else ''}\n\n"
        f"🔒 پیام قفل عضویت:\n{fj_msg[:200]}\n\n"
        f"❤️ پیام قفل واکنش:\n{rl_msg[:200]}\n\n"
        "برای تغییر:\n"
        "/setwelcome - پیام خوش‌آمدگویی\n"
        "/setforcemsg - پیام قفل عضویت\n"
        "/setreactionmsg - پیام قفل واکنش"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADMIN_PANEL),
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# آپلود (از دکمه‌های اینلاین)
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADMIN_UPLOAD_SINGLE)
async def start_upload_single_inline(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """آپلود تکی از دکمه اینلاین."""
    if not is_admin:
        return

    from handlers.upload import UploadStates

    await state.set_state(UploadStates.waiting_single_file)
    await callback.message.edit_text(
        "📤 فایل خود را ارسال کنید:",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_UPLOAD_ALBUM)
async def start_upload_album_inline(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """آپلود آلبوم از دکمه اینلاین."""
    if not is_admin:
        return

    from handlers.upload import UploadStates
    from services.file_service import FileService

    album_id = FileService.generate_album_id()
    await state.set_state(UploadStates.waiting_album_files)
    await state.update_data(album_id=album_id, files=[])
    await callback.message.edit_text(
        "📦 فایل‌ها را یکی‌یکی ارسال کنید.\nدر پایان «✅ اتمام آپلود» را بزنید.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_UPLOAD_LINK)
async def start_upload_link_inline(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """آپلود از لینک از دکمه اینلاین."""
    if not is_admin:
        return

    from handlers.upload import UploadStates

    await state.set_state(UploadStates.waiting_link)
    await callback.message.edit_text(
        "🔗 لینک مستقیم فایل را ارسال کنید:",
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# مدیریت فایل و کاربر
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADMIN_FILE_MGMT)
async def show_file_management(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """نمایش مدیریت فایل."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        "📁 **مدیریت اشتراک فایل**\n\nاز منوی زیر عمل مورد نظر را انتخاب کنید:",
        reply_markup=admin_file_management(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_BROADCAST)
async def show_broadcast_menu(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """نمایش منوی ارسال همگانی."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        "📢 **تبلیغ / ارسال همگانی**\n\nیکی از روش‌های ارسال را انتخاب کنید:",
        reply_markup=admin_broadcast_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# زیرمنوهای تنظیمات
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.SETTINGS_ON_OFF)
async def show_on_off(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """خاموش/روشن کردن ربات."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    is_on = await SettingService.get_bool(session, "bot_enabled", default=True)
    status = "🟢 روشن" if is_on else "🔴 خاموش"

    await callback.message.edit_text(
        f"🔴 **خاموش و روشن**\n\nوضعیت فعلی ربات: {status}",
        reply_markup=on_off_keyboard(is_on),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CD.SETTINGS_ON_OFF}:"))
async def toggle_bot(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    is_main_admin: bool,
    t: Callable[[str], str],
) -> None:
    """تغییر وضعیت ربات."""
    if not is_main_admin:
        await callback.answer("⛔ فقط ادمین اصلی", show_alert=True)
        return

    action = callback.data.split(":")[1]

    if action == "on":
        await SettingService.set(session, "bot_enabled", "true", "bool")
        await callback.answer(t("bot_enabled"))
    elif action == "off":
        await SettingService.set(session, "bot_enabled", "false", "bool")
        await callback.answer(t("bot_disabled"))

    is_on = await SettingService.get_bool(session, "bot_enabled", default=True)
    status = "🟢 روشن" if is_on else "🔴 خاموش"

    await callback.message.edit_text(
        f"🔴 **خاموش و روشن**\n\nوضعیت فعلی ربات: {status}",
        reply_markup=on_off_keyboard(is_on),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == CD.SETTINGS_USER_MGMT)
async def show_user_management(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """مدیریت کاربران."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        "👤 **مدیریت کاربران**\n\nاز منوی زیر عمل مورد نظر را انتخاب کنید:",
        reply_markup=admin_user_management(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.SETTINGS_USERS)
async def show_settings_users(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """👥 کاربران — خلاصه."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    users_count = await UserService.count_users(session)
    banned_count = await UserService.count_banned(session)

    text = (
        "👥 **کاربران**\n\n"
        f"📊 کل: **{users_count:,}**\n"
        f"🚫 بن‌شده: **{banned_count:,}**\n"
        f"✅ فعال: **{users_count - banned_count:,}**"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 مدیریت کاربر", callback_data=CD.SETTINGS_USER_MGMT),
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


@router.callback_query(F.data == CD.SETTINGS_BUTTONS)
async def show_button_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """مدیریت دکمه‌ها."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    show = await SettingService.get_bool(session, "show_buttons", default=True)
    btn_text = await SettingService.get(session, "button_text", "") or ""
    btn_url = await SettingService.get(session, "button_url", "") or ""

    text = (
        "🔘 **مدیریت دکمه‌ها**\n\n"
        f"وضعیت نمایش: {'✅ فعال' if show else '❌ غیرفعال'}\n"
        f"متن دکمه: {btn_text or '(تنظیم نشده)'}\n"
        f"لینک دکمه: {btn_url or '(تنظیم نشده)'}\n\n"
        "/setbtn <متن> <لینک>\n"
        "/togglebtn - فعال/غیرفعال"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADMIN_SETTINGS),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.SETTINGS_SIN)
async def show_settings_sin(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """📡 تنظیمات سین."""
    if not is_admin:
        return

    auto_read = await SettingService.get_bool(session, "auto_read_messages", default=True)

    text = (
        "📡 **تنظیمات سین**\n\n"
        f"خواندن خودکار: {'✅ فعال' if auto_read else '❌ غیرفعال'}\n\n"
        "/togglesin - تغییر وضعیت"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f"{'🔴 غیرفعال' if auto_read else '🟢 فعال'} کردن سین",
        callback_data="toggle_sin" if auto_read else "toggle_sin",
    ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADMIN_SETTINGS))

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "toggle_sin")
async def toggle_sin(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    """تغییر وضعیت سین."""
    if not is_admin:
        return
    current = await SettingService.get_bool(session, "auto_read_messages", default=True)
    await SettingService.set(session, "auto_read_messages", str(not current).lower(), "bool")
    await callback.answer("✅ تغییر کرد.")
    await show_settings_sin(callback, session, is_admin)


@router.callback_query(F.data == CD.SETTINGS_CHANNELS)
async def show_settings_channels(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """📢 تنظیمات کانال."""
    if not is_admin:
        return

    channels = await ChannelService.get_all_channels(session)
    locks = await ChannelService.get_all_reaction_locks(session)

    text = "📢 **تنظیمات کانال**\n\n🔒 قفل عضویت:\n"
    if channels:
        for ch in channels:
            s = "✅" if ch.is_active else "❌"
            text += f"  {s} {ch.display_name} (`{ch.channel_id}`)\n"
    else:
        text += "  (خالی)\n"

    text += "\n❤️ قفل واکنش:\n"
    if locks:
        for rl in locks:
            s = "✅" if rl.is_active else "❌"
            text += f"  {s} کانال `{rl.channel_id}` پیام `{rl.message_id}`\n"
    else:
        text += "  (خالی)\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔒 قفل عضویت", callback_data=CD.SETTINGS_FORCE_JOIN),
        InlineKeyboardButton(text="❤️ قفل واکنش", callback_data=CD.ADV_REACTION),
    )
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADMIN_SETTINGS))

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == CD.SETTINGS_CANCEL_FORWARD)
async def show_cancel_forward(
    callback: CallbackQuery,
    is_admin: bool,
) -> None:
    """❌ لغو فوروارد."""
    if not is_admin:
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ لغو ارسال همگانی", callback_data=CD.BROADCAST_CANCEL))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADMIN_SETTINGS))

    await callback.message.edit_text(
        "❌ **لغو فوروارد / ارسال همگانی**\n\nبا دکمه زیر ارسال در حال انجام را لغو کنید.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.SETTINGS_FILE_MGMT)
async def show_settings_file_mgmt(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """🗂 مدیریت فایل از تنظیمات."""
    if not is_admin:
        return

    files_count = await FileService.count_files(session)
    downloads = await FileService.count_total_downloads(session)

    text = (
        f"🗂 **مدیریت فایل**\n\n"
        f"📁 فایل‌ها: **{files_count:,}**\n"
        f"📥 دانلودها: **{downloads:,}**"
    )

    await callback.message.edit_text(text, reply_markup=admin_file_management(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == CD.SETTINGS_FORWARD_ALL)
async def show_forward_all(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """⏩ فوروارد همگانی."""
    if not is_admin:
        return

    from handlers.admin_broadcast import BroadcastStates
    await state.set_state(BroadcastStates.waiting_forward)
    await callback.message.edit_text(
        "⏩ **فوروارد همگانی**\n\nپیام را از کانال/گروه فوروارد کنید.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.SETTINGS_SEND_ALL)
async def show_send_all(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """📨 ارسال همگانی."""
    if not is_admin:
        return

    from handlers.admin_broadcast import BroadcastStates
    await state.set_state(BroadcastStates.waiting_text)
    await callback.message.edit_text(
        "📨 **ارسال همگانی**\n\nپیام متنی خود را بنویسید:",
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# قفل عضویت
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.SETTINGS_FORCE_JOIN)
async def show_force_join_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """قفل عضویت."""
    if not is_admin:
        return

    channels = await ChannelService.get_active_channels(session)
    text = "🔒 **قفل عضویت اجباری**\n\n"
    if channels:
        for ch in channels:
            text += f"✅ {ch.display_name} (`{ch.channel_id}`)\n"
    else:
        text += "هیچ کانال فعالی نیست.\n"

    await callback.message.edit_text(text, reply_markup=force_join_menu(), parse_mode="Markdown")
    await callback.answer()


# ═══════════════════════════════════════════════════════
# قفل واکنش
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADV_REACTION)
async def show_reaction_lock(
    callback: CallbackQuery,
    is_admin: bool,
) -> None:
    """قفل واکنش."""
    if not is_admin:
        return

    await callback.message.edit_text(
        "❤️ **قفل واکنش**\n\nاز منوی زیر عمل مورد نظر را انتخاب کنید:",
        reply_markup=reaction_lock_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# تایمر و پسورد
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADV_TIMER)
async def show_timer_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """تایمر."""
    if not is_admin:
        return

    delay = await SettingService.get_int(session, "delay_before_send", default=0)
    text = (
        f"⏱ **تایمر**\n\nتأخیر فعلی: **{delay}** ثانیه\n\n"
        "/setdelay <ثانیه>"
    )

    await callback.message.edit_text(text, reply_markup=back_button(CD.ADMIN_SETTINGS), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == CD.ADV_PASSWORD)
async def show_password_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_main_admin: bool,
) -> None:
    """پسورد."""
    if not is_main_admin:
        return

    has_pw = await SettingService.get(session, "access_password") is not None
    text = (
        f"🔑 **پسورد**\n\n"
        f"وضعیت: {'🔒 تنظیم شده' if has_pw else '🔓 ندارد'}\n\n"
        "/setpassword <پسورد>\n/clearpassword"
    )

    await callback.message.edit_text(text, reply_markup=back_button(CD.ADMIN_SETTINGS), parse_mode="Markdown")
    await callback.answer()


# ═══════════════════════════════════════════════════════
# دکمه‌های کمکی
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.CANCEL)
async def cancel_action(
    callback: CallbackQuery,
    state: FSMContext,
    t: Callable[[str], str],
) -> None:
    """لغو."""
    await state.clear()
    await callback.message.edit_text(t("operation_cancelled"))
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery) -> None:
    """دکمه خالی."""
    await callback.answer()
