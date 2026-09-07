"""
handlers/admin_panel.py — Admin panel navigation handlers.

Handles ALL inline keyboard callbacks for the admin panel.
This is the FIXED version with all missing handlers added.
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

from config import settings as app_settings
from services.user_service import UserService
from services.file_service import FileService
from services.admin_service import AdminService
from services.channel_service import ChannelService
from services.setting_service import SettingService
from keyboards.inline import (
    CD,
    admin_main_menu,
    admin_settings_menu,
    admin_advanced_settings,
    admin_broadcast_menu,
    admin_stats_keyboard,
    admin_file_management,
    admin_user_management,
    admin_admin_management,
    force_join_menu,
    reaction_lock_menu,
    on_off_keyboard,
    back_button,
)

router = Router(name="admin_panel")


# ── FSM States for sub-panel operations ─────────────
class PanelStates(StatesGroup):
    """FSM states for panel inline operations."""
    waiting_channel_id_fj = State()       # force join: add channel
    waiting_remove_channel_id = State()   # force join: remove channel
    waiting_toggle_channel_id = State()   # force join: toggle channel
    waiting_reaction_channel = State()    # reaction lock: add channel
    waiting_reaction_message = State()    # reaction lock: add message
    waiting_remove_reaction_id = State()  # reaction lock: remove
    waiting_admin_id_add = State()        # admin: add
    waiting_admin_id_remove = State()     # admin: remove
    waiting_forward_channel = State()     # forward to channel
    waiting_group_id = State()            # group settings
    waiting_sin_channel = State()         # seen settings


# ═══════════════════════════════════════════════════════
# PANEL ENTRY POINTS
# ═══════════════════════════════════════════════════════


@router.message(Command("admin"))
@router.message(F.text == "📋 پنل مدیریت")
async def open_admin_panel(
    message: Message,
    session: AsyncSession,
    t: Callable[[str], str],
    is_admin: bool,
) -> None:
    """Open the admin panel."""
    if not is_admin:
        return

    await message.answer(
        t("welcome_admin"),
        reply_markup=admin_main_menu(),
        parse_mode="Markdown",
    )


# ═══════════════════════════════════════════════════════
# MAIN PANEL NAVIGATION
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADMIN_PANEL)
async def show_admin_panel(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show the main admin panel."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        t("welcome_admin"),
        reply_markup=admin_main_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_SETTINGS)
async def show_settings(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show settings menu."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        "⚙️ **تنظیمات کلی**\n\nاز منوی زیر بخش مورد نظر را انتخاب کنید:",
        reply_markup=admin_settings_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_STATS)
async def show_stats(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show bot statistics."""
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


@router.callback_query(F.data == CD.ADMIN_CAPTION)
async def show_caption_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show caption settings."""
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
    """Show text customization settings."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    welcome = await SettingService.get(session, "welcome_message", "")
    fj_msg = await SettingService.get(session, "force_join_message", "")
    rl_msg = await SettingService.get(session, "reaction_lock_message", "")

    text = (
        "📝 **تنظیم متون ربات**\n\n"
        f"👋 پیام خوش‌آمدگویی:\n{welcome[:200]}{'...' if len(str(welcome)) > 200 else ''}\n\n"
        f"🔒 پیام قفل عضویت:\n{fj_msg[:200]}\n\n"
        f"❤️ پیام قفل واکنش:\n{rl_msg[:200]}\n\n"
        "برای تغییر هر کدام، دستور مربوطه را ارسال کنید:\n"
        "/setwelcome - تنظیم پیام خوش‌آمدگویی\n"
        "/setforcemsg - تنظیم پیام قفل عضویت\n"
        "/setreactionmsg - تنظیم پیام قفل واکنش"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADMIN_PANEL),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_FILE_MGMT)
async def show_file_management(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show file management menu."""
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
    """Show broadcast menu."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        "📢 **تبلیغ / ارسال همگانی**\n\n"
        "یکی از روش‌های ارسال را انتخاب کنید:",
        reply_markup=admin_broadcast_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# ✅ FIX #1: Upload inline buttons (were missing)
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADMIN_UPLOAD_SINGLE)
async def start_upload_single_inline(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Handle single upload button from inline keyboard."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    from keyboards.reply import cancel_keyboard
    from handlers.upload import UploadStates

    await state.set_state(UploadStates.waiting_single_file)
    await callback.message.edit_text(
        "📤 **آپلود تکی**\n\nلطفاً فایل مورد نظر خود را ارسال کنید.",
        parse_mode="Markdown",
    )
    await callback.message.answer(
        "📄 فایل خود را ارسال کنید:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_UPLOAD_ALBUM)
async def start_upload_album_inline(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Handle album upload button from inline keyboard."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    from keyboards.reply import done_keyboard
    from handlers.upload import UploadStates
    from services.file_service import FileService

    album_id = FileService.generate_album_id()
    await state.set_state(UploadStates.waiting_album_files)
    await state.update_data(album_id=album_id, files=[])
    await callback.message.edit_text(
        "📦 **آپلود گروهی**\n\nفایل‌ها را یکی‌یکی ارسال کنید و در پایان «اتمام آپلود» را بزنید.",
        parse_mode="Markdown",
    )
    await callback.message.answer(
        "📦 فایل‌ها را ارسال کنید:",
        reply_markup=done_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_UPLOAD_LINK)
async def start_upload_link_inline(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Handle link upload button from inline keyboard."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    from keyboards.reply import cancel_keyboard
    from handlers.upload import UploadStates

    await state.set_state(UploadStates.waiting_link)
    await callback.message.edit_text(
        "🔗 **آپلود از لینک**\n\nلطفاً لینک مستقیم فایل را ارسال کنید:",
        parse_mode="Markdown",
    )
    await callback.message.answer(
        "🔗 لینک فایل را ارسال کنید:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# ✅ FIX #2: Settings sub-menus that were MISSING handlers
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.SETTINGS_USERS)
async def show_settings_users(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """👥 کاربران — Show user list summary."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    users_count = await UserService.count_users(session)
    banned_count = await UserService.count_banned(session)

    text = (
        "👥 **کاربران**\n\n"
        f"📊 تعداد کل: **{users_count:,}**\n"
        f"🚫 بن‌شده: **{banned_count:,}**\n"
        f"✅ فعال: **{users_count - banned_count:,}**\n\n"
        "از دکمه زیر برای مدیریت کاربران استفاده کنید:"
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


@router.callback_query(F.data == CD.SETTINGS_CHANNEL)
async def show_settings_channel(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """📤 ارسال به کانال — Forward/send a message to a specific channel."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    # Get configured channel
    forward_channel = await SettingService.get(session, "forward_channel_id", "")

    text = (
        "📤 **ارسال به کانال**\n\n"
        f"کانال فعلی: `{forward_channel or 'تنظیم نشده'}`\n\n"
        "برای تنظیم کانال مقصد:\n"
        "/setforwardchannel <channel_id>\n\n"
        "برای ارسال پیام به کانال، از منوی اصلی ارسال همگانی استفاده کنید."
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADMIN_SETTINGS),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.SETTINGS_GROUP)
async def show_settings_group(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """💬 گروه — Group settings."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    group_id = await SettingService.get(session, "group_id", "")

    text = (
        "💬 **تنظیمات گروه**\n\n"
        f"آیدی گروه فعلی: `{group_id or 'تنظیم نشده'}`\n\n"
        "برای تنظیم گروه:\n"
        "/setgroup <group_id>\n\n"
        "ربات می‌تواند در گروه مشخص‌شده فعالیت کند."
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
    t: Callable[[str], str],
) -> None:
    """📡 تنظیمات سین (Seen/Read receipt settings)."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    auto_read = await SettingService.get_bool(session, "auto_read_messages", default=True)

    text = (
        "📡 **تنظیمات سین**\n\n"
        f"خواندن خودکار پیام‌ها: {'✅ فعال' if auto_read else '❌ غیرفعال'}\n\n"
        "وقتی فعال باشد، ربات به صورت خودکار پیام‌های دریافتی را به عنوان خوانده‌شده علامت‌گذاری می‌کند.\n\n"
        "برای تغییر:\n"
        "/togglesin - فعال/غیرفعال کردن"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    if auto_read:
        builder.row(InlineKeyboardButton(
            text="🔴 غیرفعال کردن سین", callback_data="toggle_sin:off"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="🟢 فعال کردن سین", callback_data="toggle_sin:on"
        ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADMIN_SETTINGS))

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_sin:"))
async def toggle_sin(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Toggle seen/read settings."""
    if not is_admin:
        return

    action = callback.data.split(":")[1]
    new_val = action == "on"
    await SettingService.set(session, "auto_read_messages", str(new_val).lower(), "bool")

    # Refresh the display
    text = (
        "📡 **تنظیمات سین**\n\n"
        f"خواندن خودکار پیام‌ها: {'✅ فعال' if new_val else '❌ غیرفعال'}\n\n"
        "برای تغییر:\n"
        "/togglesin - فعال/غیرفعال کردن"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    if new_val:
        builder.row(InlineKeyboardButton(
            text="🔴 غیرفعال کردن سین", callback_data="toggle_sin:off"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="🟢 فعال کردن سین", callback_data="toggle_sin:on"
        ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADMIN_SETTINGS))

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer("✅ تنظیمات بروزرسانی شد")


@router.callback_query(F.data == CD.SETTINGS_CHANNELS)
async def show_settings_channels(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """📢 تنظیمات کانال — Show channel settings and list."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    channels = await ChannelService.get_all_channels(session)
    reaction_locks = await ChannelService.get_all_reaction_locks(session)

    text = "📢 **تنظیمات کانال**\n\n"

    # Force Join channels
    text += "🔒 **کانال‌های قفل عضویت:**\n"
    if channels:
        for i, ch in enumerate(channels, 1):
            status = "✅" if ch.is_active else "❌"
            text += f"  {i}. {status} {ch.display_name} (`{ch.channel_id}`)\n"
    else:
        text += "  (هیچ کانالی تنظیم نشده)\n"

    # Reaction locks
    text += "\n❤️ **قفل‌های واکنش:**\n"
    if reaction_locks:
        for i, rl in enumerate(reaction_locks, 1):
            status = "✅" if rl.is_active else "❌"
            text += f"  {i}. {status} کانال `{rl.channel_id}` - پیام `{rl.message_id}`\n"
    else:
        text += "  (قفل واکنشی تنظیم نشده)\n"

    text += "\nاز دکمه‌های زیر برای مدیریت استفاده کنید:"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔒 قفل عضویت", callback_data=CD.SETTINGS_FORCE_JOIN),
        InlineKeyboardButton(text="❤️ قفل واکنش", callback_data=CD.ADV_REACTION),
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


@router.callback_query(F.data == CD.SETTINGS_CANCEL_FORWARD)
async def show_cancel_forward(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """❌ لغو فوروارد / همگانی — Cancel any ongoing broadcast."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    text = (
        "❌ **لغو فوروارد / ارسال همگانی**\n\n"
        "اگر ارسال همگانی یا فورواردی در حال انجام است، با دکمه زیر لغو کنید.\n\n"
        "⚠️ توجه: این عملیات فقط ارسال‌های در حال انجام را متوقف می‌کند."
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ لغو ارسال همگانی", callback_data=CD.BROADCAST_CANCEL),
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


@router.callback_query(F.data == CD.SETTINGS_FILE_MGMT)
async def show_settings_file_mgmt(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """🗂 مدیریت فایل — Show file management from settings menu."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    files_count = await FileService.count_files(session)
    downloads_count = await FileService.count_total_downloads(session)

    text = (
        "🗂 **مدیریت فایل**\n\n"
        f"📁 تعداد فایل‌ها: **{files_count:,}**\n"
        f"📥 کل دانلودها: **{downloads_count:,}**\n\n"
        "از منوی زیر عمل مورد نظر را انتخاب کنید:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=admin_file_management(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.SETTINGS_FORWARD_ALL)
async def show_forward_all(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """⏩ فوروارد همگانی — Start forward to all users."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    from handlers.admin_broadcast import BroadcastStates

    await state.set_state(BroadcastStates.waiting_forward)
    await callback.message.edit_text(
        "⏩ **فوروارد همگانی**\n\n"
        "لطفاً پیام مورد نظر را از کانال یا گروه به ربات فوروارد کنید.\n\n"
        "پیام فورواردشده به تمام کاربران ارسال خواهد شد.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.SETTINGS_SEND_ALL)
async def show_send_all(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """📨 ارسال همگانی — Start send to all users."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    from handlers.admin_broadcast import BroadcastStates

    await state.set_state(BroadcastStates.waiting_text)
    await callback.message.edit_text(
        "📨 **ارسال همگانی**\n\n"
        "لطفاً پیام متنی مورد نظر برای ارسال به همه کاربران را بنویسید.\n\n"
        "از HTML می‌توانید استفاده کنید.",
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# ON/OFF SETTINGS
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.SETTINGS_ON_OFF)
async def show_on_off(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show bot on/off toggle."""
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
    """Toggle bot on/off."""
    if not is_main_admin:
        await callback.answer("⛔ فقط ادمین اصلی می‌تواند ربات را خاموش/روشن کند.", show_alert=True)
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


@router.callback_query(F.data == CD.SETTINGS_FORCE_JOIN)
async def show_force_join_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show force join management menu."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    channels = await ChannelService.get_active_channels(session)

    text = "🔒 **مدیریت قفل عضویت اجباری**\n\n"
    if channels:
        text += "کانال‌های فعال:\n"
        for ch in channels:
            text += f"  ✅ {ch.display_name} (`{ch.channel_id}`)\n"
    else:
        text += "هیچ کانال فعالی وجود ندارد.\n"

    await callback.message.edit_text(
        text,
        reply_markup=force_join_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.SETTINGS_USER_MGMT)
async def show_user_management(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show user management menu."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        "👤 **مدیریت کاربران**\n\nاز منوی زیر عمل مورد نظر را انتخاب کنید:",
        reply_markup=admin_user_management(),
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
    """Show button settings."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    show = await SettingService.get_bool(session, "show_buttons", default=True)
    btn_text = await SettingService.get(session, "button_text", "")
    btn_url = await SettingService.get(session, "button_url", "")

    text = (
        "🔘 **مدیریت دکمه‌ها**\n\n"
        f"وضعیت نمایش: {'✅ فعال' if show else '❌ غیرفعال'}\n"
        f"متن دکمه: {btn_text or '(تنظیم نشده)'}\n"
        f"لینک دکمه: {btn_url or '(تنظیم نشده)'}\n\n"
        "برای تنظیم:\n"
        "/setbtn <متن> <لینک>\n"
        "/togglebtn - فعال/غیرفعال کردن"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADMIN_SETTINGS),
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# ✅ FIX #3: Force Join sub-menu handlers (were missing)
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.FJ_ADD)
async def fj_add_channel(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """➕ افزودن کانال به قفل عضویت."""
    if not is_admin:
        return

    await state.set_state(PanelStates.waiting_channel_id_fj)
    await callback.message.edit_text(
        "➕ **افزودن کانال به قفل عضویت**\n\n"
        "لطفاً آیدی عددی کانال را وارد کنید:\n\n"
        "مثال: `-1001234567890`\n"
        "یا نام کاربری: `@channel_username`",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(PanelStates.waiting_channel_id_fj)
async def process_fj_add_channel(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Process channel ID for force join add."""
    text = message.text.strip()
    channel_id = None
    channel_username = None

    # Try as numeric ID
    try:
        channel_id = int(text)
    except ValueError:
        # Try as username
        if text.startswith("@"):
            channel_username = text[1:]
        elif text.startswith("https://t.me/"):
            channel_username = text.split("/")[-1]
        else:
            channel_username = text

    # Resolve username to ID
    if channel_username and not channel_id:
        from utils.telegram import get_chat_info
        chat_info = await get_chat_info(bot, channel_username)
        if chat_info:
            channel_id = chat_info["id"]
        else:
            await message.answer("⚠️ کانال یافت نشد. لطفاً آیدی عددی را وارد کنید.")
            return

    if not channel_id:
        await message.answer("⚠️ آیدی نامعتبر است.")
        return

    # Get channel info
    from utils.telegram import get_chat_info
    chat_info = await get_chat_info(bot, channel_id)

    await ChannelService.add_channel(
        session=session,
        channel_id=channel_id,
        channel_username=channel_username,
        channel_title=chat_info.get("title") if chat_info else None,
        invite_link=chat_info.get("invite_link") if chat_info else None,
    )

    await state.clear()
    title = chat_info.get("title", str(channel_id)) if chat_info else str(channel_id)

    from keyboards.reply import admin_reply_menu
    await message.answer(
        f"✅ **کانال اضافه شد:**\n\n"
        f"📢 عنوان: {title}\n"
        f"🆔 آیدی: `{channel_id}`",
        parse_mode="Markdown",
        reply_markup=admin_reply_menu(),
    )


@router.callback_query(F.data == CD.FJ_REMOVE)
async def fj_remove_channel(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """➖ حذف کانال از قفل عضویت."""
    if not is_admin:
        return

    channels = await ChannelService.get_all_channels(session)
    if not channels:
        await callback.answer("⚠️ هیچ کانالی تنظیم نشده است.", show_alert=True)
        return

    # Show list with remove buttons
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for ch in channels:
        status = "✅" if ch.is_active else "❌"
        builder.row(InlineKeyboardButton(
            text=f"🗑 {status} {ch.display_name} ({ch.channel_id})",
            callback_data=f"fj_remove_confirm:{ch.channel_id}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.SETTINGS_FORCE_JOIN))

    await callback.message.edit_text(
        "➖ **حذف کانال از قفل عضویت**\n\nکانال مورد نظر را انتخاب کنید:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fj_remove_confirm:"))
async def fj_remove_confirm(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Confirm and remove a force join channel."""
    if not is_admin:
        return

    channel_id = int(callback.data.split(":")[1])
    removed = await ChannelService.remove_channel(session, channel_id)

    if removed:
        await callback.answer(f"✅ کانال {channel_id} حذف شد.", show_alert=True)
    else:
        await callback.answer("⚠️ کانال یافت نشد.", show_alert=True)

    # Refresh the list
    await fj_remove_channel(callback, None, session, is_admin)


@router.callback_query(F.data == CD.FJ_LIST)
async def fj_list_channels(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """📋 لیست کانال‌های قفل عضویت."""
    if not is_admin:
        return

    channels = await ChannelService.get_all_channels(session)

    if not channels:
        text = "📋 **لیست کانال‌های قفل عضویت:**\n\n⚠️ هیچ کانالی تنظیم نشده است."
    else:
        text = "📋 **لیست کانال‌های قفل عضویت:**\n\n"
        for i, ch in enumerate(channels, 1):
            status = "✅ فعال" if ch.is_active else "❌ غیرفعال"
            text += (
                f"{i}. {ch.display_name}\n"
                f"   🆔 `{ch.channel_id}`\n"
                f"   📊 {status}\n"
                f"   🔗 {ch.join_link}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.SETTINGS_FORCE_JOIN),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.FJ_TOGGLE)
async def fj_toggle_channel(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """🔄 فعال/غیرفعال کردن کانال قفل."""
    if not is_admin:
        return

    channels = await ChannelService.get_all_channels(session)
    if not channels:
        await callback.answer("⚠️ هیچ کانالی تنظیم نشده است.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for ch in channels:
        status = "✅" if ch.is_active else "❌"
        toggle_text = "🔴 غیرفعال" if ch.is_active else "🟢 فعال"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {ch.display_name}",
                callback_data="noop",
            ),
            InlineKeyboardButton(
                text=toggle_text,
                callback_data=f"fj_toggle_confirm:{ch.channel_id}",
            ),
        )
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.SETTINGS_FORCE_JOIN))

    await callback.message.edit_text(
        "🔄 **فعال/غیرفعال کردن کانال‌ها**\n\nدکمه مربوط به هر کانال را بزنید:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fj_toggle_confirm:"))
async def fj_toggle_confirm(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Toggle a specific channel."""
    if not is_admin:
        return

    channel_id = int(callback.data.split(":")[1])
    new_state = await ChannelService.toggle_channel(session, channel_id)

    if new_state is not None:
        status = "فعال" if new_state else "غیرفعال"
        await callback.answer(f"✅ کانال {status} شد.")
    else:
        await callback.answer("⚠️ کانال یافت نشد.", show_alert=True)

    # Refresh
    await fj_toggle_channel(callback, session, is_admin)


# ═══════════════════════════════════════════════════════
# ✅ FIX #4: Reaction Lock sub-menu handlers (were missing)
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.RL_ADD)
async def rl_add_lock(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """➕ افزودن قفل واکنش."""
    if not is_admin:
        return

    await state.set_state(PanelStates.waiting_reaction_channel)
    await callback.message.edit_text(
        "➕ **افزودن قفل واکنش**\n\n"
        "لطفاً آیدی عددی کانال حاوی پست مورد نظر را وارد کنید:\n\n"
        "مثال: `-1001234567890`",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(PanelStates.waiting_reaction_channel)
async def process_rl_channel(
    message: Message,
    state: FSMContext,
) -> None:
    """Process reaction lock channel ID."""
    try:
        channel_id = int(message.text.strip())
        await state.update_data(reaction_channel_id=channel_id)
        await state.set_state(PanelStates.waiting_reaction_message)
        await message.answer("💬 لطفاً آیدی پیام مورد نظر را وارد کنید:")
    except ValueError:
        await message.answer("⚠️ آیدی نامعتبر. لطفاً یک عدد صحیح وارد کنید.")


@router.message(PanelStates.waiting_reaction_message)
async def process_rl_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Process reaction lock message ID."""
    try:
        message_id = int(message.text.strip())
        data = await state.get_data()
        channel_id = data.get("reaction_channel_id")

        await ChannelService.add_reaction_lock(
            session=session,
            channel_id=channel_id,
            message_id=message_id,
        )

        await state.clear()
        from keyboards.reply import admin_reply_menu
        await message.answer(
            f"✅ **قفل واکنش اضافه شد:**\n\n"
            f"📢 کانال: `{channel_id}`\n"
            f"💬 پیام: `{message_id}`",
            parse_mode="Markdown",
            reply_markup=admin_reply_menu(),
        )
    except ValueError:
        await message.answer("⚠️ آیدی نامعتبر.")


@router.callback_query(F.data == CD.RL_REMOVE)
async def rl_remove_lock(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """➖ حذف قفل واکنش."""
    if not is_admin:
        return

    locks = await ChannelService.get_all_reaction_locks(session)
    if not locks:
        await callback.answer("⚠️ قفل واکنشی وجود ندارد.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for lock in locks:
        status = "✅" if lock.is_active else "❌"
        builder.row(InlineKeyboardButton(
            text=f"🗑 {status} کانال `{lock.channel_id}` - پیام `{lock.message_id}`",
            callback_data=f"rl_remove_confirm:{lock.id}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADV_REACTION))

    await callback.message.edit_text(
        "➖ **حذف قفل واکنش**\n\nقفل مورد نظر را انتخاب کنید:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rl_remove_confirm:"))
async def rl_remove_confirm(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Confirm and remove a reaction lock."""
    if not is_admin:
        return

    lock_id = int(callback.data.split(":")[1])
    removed = await ChannelService.remove_reaction_lock(session, lock_id)

    if removed:
        await callback.answer("✅ قفل واکنش حذف شد.", show_alert=True)
    else:
        await callback.answer("⚠️ قفل یافت نشد.", show_alert=True)

    # Refresh
    await rl_remove_lock(callback, session, is_admin)


@router.callback_query(F.data == CD.RL_LIST)
async def rl_list_locks(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """📋 لیست قفل‌های واکنش."""
    if not is_admin:
        return

    locks = await ChannelService.get_all_reaction_locks(session)

    if not locks:
        text = "📋 **لیست قفل‌های واکنش:**\n\n⚠️ قفل واکنشی تنظیم نشده است."
    else:
        text = "📋 **لیست قفل‌های واکنش:**\n\n"
        for i, lock in enumerate(locks, 1):
            status = "✅ فعال" if lock.is_active else "❌ غیرفعال"
            emoji = lock.reaction_emoji or "هر واکنشی"
            text += (
                f"{i}. کانال: `{lock.channel_id}`\n"
                f"   💬 پیام: `{lock.message_id}`\n"
                f"   😀 واکنش: {emoji}\n"
                f"   📊 {status}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADV_REACTION),
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# ✅ FIX #5: Admin Management sub-menu handlers (were missing)
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADV_ADMIN_MGMT)
async def show_admin_management(
    callback: CallbackQuery,
    is_admin: bool,
    is_main_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show admin management menu."""
    if not is_main_admin:
        await callback.answer("⛔ فقط ادمین اصلی می‌تواند ادمین‌ها را مدیریت کند.", show_alert=True)
        return

    await callback.message.edit_text(
        "👑 **مدیریت ادمین‌ها**\n\nاز منوی زیر عمل مورد نظر را انتخاب کنید:",
        reply_markup=admin_admin_management(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_ADD)
async def admin_add_start(
    callback: CallbackQuery,
    state: FSMContext,
    is_main_admin: bool,
) -> None:
    """➕ افزودن ادمین."""
    if not is_main_admin:
        await callback.answer("⛔ فقط ادمین اصلی", show_alert=True)
        return

    await state.set_state(PanelStates.waiting_admin_id_add)
    await callback.message.edit_text(
        "➕ **افزودن ادمین جدید**\n\n"
        "لطفاً آیدی عددی کاربر مورد نظر را وارد کنید:",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(PanelStates.waiting_admin_id_add)
async def process_admin_add(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Process admin add."""
    try:
        user_id = int(message.text.strip())
        admin = await AdminService.add_admin(session, user_id)
        await state.clear()
        from keyboards.reply import admin_reply_menu
        await message.answer(
            f"✅ **ادمین جدید اضافه شد:**\n\n"
            f"🆔 آیدی: `{user_id}`",
            parse_mode="Markdown",
            reply_markup=admin_reply_menu(),
        )
    except ValueError:
        await message.answer("⚠️ آیدی نامعتبر.")


@router.callback_query(F.data == CD.ADMIN_REMOVE)
async def admin_remove_start(
    callback: CallbackQuery,
    session: AsyncSession,
    is_main_admin: bool,
) -> None:
    """➖ حذف ادمین."""
    if not is_main_admin:
        await callback.answer("⛔ فقط ادمین اصلی", show_alert=True)
        return

    admins = await AdminService.get_all_admins(session)
    # Filter out main admin
    removable = [a for a in admins if not a.is_main_admin]

    if not removable:
        await callback.answer("⚠️ ادمین دیگری وجود ندارد.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for admin in removable:
        builder.row(InlineKeyboardButton(
            text=f"🗑 `{admin.user_id}` - {admin.full_name or 'N/A'}",
            callback_data=f"admin_remove_confirm:{admin.user_id}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADV_ADMIN_MGMT))

    await callback.message.edit_text(
        "➖ **حذف ادمین**\n\nادمین مورد نظر را انتخاب کنید:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_remove_confirm:"))
async def admin_remove_confirm(
    callback: CallbackQuery,
    session: AsyncSession,
    is_main_admin: bool,
) -> None:
    """Confirm admin removal."""
    if not is_main_admin:
        return

    user_id = int(callback.data.split(":")[1])
    removed = await AdminService.remove_admin(session, user_id)

    if removed:
        await callback.answer(f"✅ ادمین {user_id} حذف شد.", show_alert=True)
    else:
        await callback.answer("⚠️ ادمین یافت نشد یا ادمین اصلی است.", show_alert=True)

    # Refresh
    await admin_remove_start(callback, session, is_main_admin)


@router.callback_query(F.data == CD.ADMIN_LIST)
async def admin_list_show(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """📋 لیست ادمین‌ها."""
    if not is_admin:
        return

    admins = await AdminService.get_all_admins(session)

    text = "👑 **لیست ادمین‌ها:**\n\n"
    for i, admin in enumerate(admins, 1):
        role = "⭐ اصلی" if admin.is_main_admin else "👤"
        perms = []
        if admin.can_upload:
            perms.append("📤")
        if admin.can_broadcast:
            perms.append("📢")
        if admin.can_manage_users:
            perms.append("👥")
        if admin.can_manage_settings:
            perms.append("⚙️")
        text += f"{i}. {role} `{admin.user_id}` - {admin.full_name or 'N/A'}\n   {''.join(perms)}\n"

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADV_ADMIN_MGMT),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_PERMS)
async def admin_perms_show(
    callback: CallbackQuery,
    session: AsyncSession,
    is_main_admin: bool,
) -> None:
    """🔑 تنظیم دسترسی‌های ادمین."""
    if not is_main_admin:
        await callback.answer("⛔ فقط ادمین اصلی", show_alert=True)
        return

    admins = await AdminService.get_all_admins(session)
    removable = [a for a in admins if not a.is_main_admin]

    if not removable:
        await callback.answer("⚠️ ادمین دیگری وجود ندارد.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for admin in removable:
        builder.row(InlineKeyboardButton(
            text=f"🔑 `{admin.user_id}` - {admin.full_name or 'N/A'}",
            callback_data=f"admin_perms_edit:{admin.user_id}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADV_ADMIN_MGMT))

    await callback.message.edit_text(
        "🔑 **تنظیم دسترسی‌ها**\n\nادمین مورد نظر را انتخاب کنید:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_perms_edit:"))
async def admin_perms_edit(
    callback: CallbackQuery,
    session: AsyncSession,
    is_main_admin: bool,
) -> None:
    """Edit permissions for a specific admin."""
    if not is_main_admin:
        return

    user_id = int(callback.data.split(":")[1])
    admin = await AdminService.get_admin(session, user_id)

    if not admin:
        await callback.answer("⚠️ ادمین یافت نشد.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    # Toggle permissions
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if admin.can_upload else '❌'} آپلود فایل",
            callback_data=f"admin_perm_toggle:{user_id}:upload",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if admin.can_broadcast else '❌'} ارسال همگانی",
            callback_data=f"admin_perm_toggle:{user_id}:broadcast",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if admin.can_manage_users else '❌'} مدیریت کاربران",
            callback_data=f"admin_perm_toggle:{user_id}:users",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if admin.can_manage_settings else '❌'} مدیریت تنظیمات",
            callback_data=f"admin_perm_toggle:{user_id}:settings",
        ),
    )
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADMIN_PERMS))

    await callback.message.edit_text(
        f"🔑 **دسترسی‌های ادمین `{user_id}`:**\n\n"
        f"👤 نام: {admin.full_name or 'N/A'}\n\n"
        "هر دسترسی را با دکمه مربوطه فعال/غیرفعال کنید:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_perm_toggle:"))
async def admin_perm_toggle(
    callback: CallbackQuery,
    session: AsyncSession,
    is_main_admin: bool,
) -> None:
    """Toggle a specific permission for an admin."""
    if not is_main_admin:
        return

    parts = callback.data.split(":")
    user_id = int(parts[1])
    perm = parts[2]

    admin = await AdminService.get_admin(session, user_id)
    if not admin:
        await callback.answer("⚠️ ادمین یافت نشد.", show_alert=True)
        return

    # Toggle the permission
    perm_map = {
        "upload": "can_upload",
        "broadcast": "can_broadcast",
        "users": "can_manage_users",
        "settings": "can_manage_settings",
    }

    if perm in perm_map:
        current = getattr(admin, perm_map[perm])
        await AdminService.update_permissions(
            session, user_id, **{perm_map[perm]: not current}
        )
        await callback.answer("✅ دسترسی تغییر کرد.")

    # Refresh
    await admin_perms_edit(callback, session, is_main_admin)


# ═══════════════════════════════════════════════════════
# ADVANCED SETTINGS HANDLERS
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADV_FORCE_JOIN)
async def show_force_join_advanced(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show force join settings from advanced menu."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        "🔒 **قفل جوین اجباری**\n\nاز منوی زیر عمل مورد نظر را انتخاب کنید:",
        reply_markup=force_join_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADV_REACTION)
async def show_reaction_lock_advanced(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show reaction lock settings from advanced menu."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        "❤️ **قفل واکنش**\n\nاز منوی زیر عمل مورد نظر را انتخاب کنید:",
        reply_markup=reaction_lock_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADV_TIMER)
async def show_timer_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show timer settings."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    delay = await SettingService.get_int(session, "delay_before_send", default=0)

    text = (
        "⏱ **تنظیمات تایمر**\n\n"
        f"تأخیر فعلی: **{delay}** ثانیه\n\n"
        "برای تغییر، عدد مورد نظر (به ثانیه) را ارسال کنید:\n"
        "/setdelay <ثانیه>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADMIN_SETTINGS),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADV_PASSWORD)
async def show_password_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    is_main_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show password settings."""
    if not is_main_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    has_password = await SettingService.get(session, "access_password") is not None

    text = (
        "🔑 **تنظیم پسورد**\n\n"
        f"وضعیت: {'🔒 تنظیم شده' if has_password else '🔓 تنظیم نشده'}\n\n"
        "برای تنظیم پسورد جدید:\n"
        "/setpassword <پسورد>\n\n"
        "برای حذف پسورد:\n"
        "/clearpassword"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADMIN_SETTINGS),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADV_ON_OFF)
async def show_on_off_advanced(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show on/off from advanced menu (redirects to main on/off)."""
    await show_on_off(callback, session, is_admin, t)


@router.callback_query(F.data == CD.ADV_USER_MGMT)
async def show_user_mgmt_advanced(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show user management from advanced menu."""
    await show_user_management(callback, is_admin, t)


@router.callback_query(F.data == CD.ADV_DELETE_FILE)
async def show_delete_file_advanced(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show file deletion from advanced menu."""
    if not is_admin:
        return
    await callback.message.edit_text(
        "🗑 **حذف فایل**\n\nاز منوی مدیریت فایل استفاده کنید:",
        reply_markup=admin_file_management(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADV_FORWARD)
async def show_forward_advanced(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """⏩ فوروارد همگانی from advanced menu."""
    if not is_admin:
        return

    from handlers.admin_broadcast import BroadcastStates
    await state.set_state(BroadcastStates.waiting_forward)
    await callback.message.edit_text(
        "⏩ **فوروارد همگانی**\n\n"
        "لطفاً پیام مورد نظر را از کانال یا گروه فوروارد کنید.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADV_SEND)
async def show_send_advanced(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """📨 ارسال همگانی from advanced menu."""
    if not is_admin:
        return

    from handlers.admin_broadcast import BroadcastStates
    await state.set_state(BroadcastStates.waiting_text)
    await callback.message.edit_text(
        "📨 **ارسال همگانی**\n\n"
        "لطفاً پیام متنی مورد نظر را بنویسید.",
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# MISC HANDLERS
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.CANCEL)
async def cancel_action(
    callback: CallbackQuery,
    state: FSMContext,
    t: Callable[[str], str],
) -> None:
    """Generic cancel action."""
    await state.clear()
    await callback.message.edit_text(t("operation_cancelled"))
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery) -> None:
    """Handle no-op button presses."""
    await callback.answer()
