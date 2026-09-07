"""
handlers/admin_panel.py — Admin panel navigation handlers.

Handles all inline keyboard callbacks for the admin panel.
"""

from __future__ import annotations

from typing import Callable

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
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
    admin_advanced_settings,
    admin_broadcast_menu,
    admin_stats_keyboard,
    admin_file_management,
    admin_user_management,
    admin_admin_management,
    force_join_menu,
    reaction_lock_menu,
    on_off_keyboard,
)

router = Router(name="admin_panel")

# ═══════════════════════════════════════════════════════
# PANEL ENTRY POINTS (command + reply keyboard)
# The bot menu exposes /admin (label: «پنل مدیریت») and the
# reply keyboard shows «📋 پنل مدیریت» — but no message
# handler existed for them, so pressing them silently did
# nothing. These handlers open the same inline panel that
# /start shows to admins.
# ═══════════════════════════════════════════════════════


@router.message(Command("admin"))
@router.message(F.text == "📋 پنل مدیریت")
async def open_admin_panel(
    message: Message,
    t: Callable[[str], str],
    is_admin: bool,
) -> None:
    """Open the admin panel (from /admin command or reply button)."""
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


@router.callback_query(F.data == CD.ADMIN_UPLOAD)
async def show_upload_menu(
    callback: CallbackQuery,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show upload options menu."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        "📤 **منوی آپلود**\n\nیکی از روش‌های آپلود را انتخاب کنید:",
        reply_markup=admin_main_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


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
        "از /clear برای حذف کپشن استفاده کنید."
    )

    from keyboards.inline import back_button
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
        f"👋 پیام خوش‌آمدگویی:\n{welcome[:200]}{'...' if len(welcome) > 200 else ''}\n\n"
        f"🔒 پیام قفل عضویت:\n{fj_msg[:200]}\n\n"
        f"❤️ پیام قفل واکنش:\n{rl_msg[:200]}\n\n"
        "برای تغییر هر کدام، دستور مربوطه را ارسال کنید:\n"
        "/setwelcome - تنظیم پیام خوش‌آمدگویی\n"
        "/setforcemsg - تنظیم پیام قفل عضویت\n"
        "/setreactionmsg - تنظیم پیام قفل واکنش"
    )

    from keyboards.inline import back_button
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
# SETTINGS SUB-MENUS
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

    # Refresh the on/off menu
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
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show force join management menu."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await callback.message.edit_text(
        "🔒 **مدیریت قفل عضویت اجباری**\n\n"
        "کانال‌هایی که کاربر باید قبل از استفاده از ربات عضو آن‌ها شود:",
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


# ═══════════════════════════════════════════════════════
# ADVANCED SETTINGS
# ═══════════════════════════════════════════════════════


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

    from keyboards.inline import back_button
    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADMIN_SETTINGS),
        parse_mode="Markdown",
    )
    await callback.answer()


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

    from keyboards.inline import back_button
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

    from keyboards.inline import back_button
    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADMIN_SETTINGS),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == CD.CANCEL)
async def cancel_action(
    callback: CallbackQuery,
    t: Callable[[str], str],
) -> None:
    """Generic cancel action."""
    await callback.message.edit_text(t("operation_cancelled"))
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery) -> None:
    """Handle no-op button presses (e.g., page counter)."""
    await callback.answer()
