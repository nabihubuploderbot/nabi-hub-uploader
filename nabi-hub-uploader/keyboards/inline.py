"""
keyboards/inline.py — All Inline Keyboard Markups.

Centralized keyboard factory for the admin panel and user interactions.
"""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ── Callback Data Prefixes ──────────────────────────
class CD:
    """Callback data constants."""

    # Admin Panel Navigation
    ADMIN_PANEL = "admin_panel"
    ADMIN_SETTINGS = "admin_settings"
    ADMIN_UPLOAD = "admin_upload"
    ADMIN_UPLOAD_SINGLE = "admin_upload_single"
    ADMIN_UPLOAD_ALBUM = "admin_upload_album"
    ADMIN_UPLOAD_LINK = "admin_upload_link"
    ADMIN_BROADCAST = "admin_broadcast"
    ADMIN_STATS = "admin_stats"
    ADMIN_CAPTION = "admin_caption"
    ADMIN_TEXTS = "admin_texts"
    ADMIN_FILE_MGMT = "admin_file_mgmt"
    ADMIN_BACK = "admin_back"

    # Settings Sub-menus
    SETTINGS_USERS = "settings_users"
    SETTINGS_CHANNEL = "settings_channel"
    SETTINGS_GROUP = "settings_group"
    SETTINGS_BUTTONS = "settings_buttons"
    SETTINGS_SIN = "settings_sin"
    SETTINGS_CHANNELS = "settings_channels"
    SETTINGS_FORCE_JOIN = "settings_force_join"
    SETTINGS_CANCEL_FORWARD = "settings_cancel_forward"
    SETTINGS_FILE_MGMT = "settings_file_mgmt"
    SETTINGS_FORWARD_ALL = "settings_forward_all"
    SETTINGS_SEND_ALL = "settings_send_all"
    SETTINGS_ON_OFF = "settings_on_off"
    SETTINGS_USER_MGMT = "settings_user_mgmt"

    # Advanced Settings
    ADV_FORWARD = "adv_forward"
    ADV_SEND = "adv_send"
    ADV_ON_OFF = "adv_on_off"
    ADV_USER_MGMT = "adv_user_mgmt"
    ADV_DELETE_FILE = "adv_delete_file"
    ADV_TIMER = "adv_timer"
    ADV_PASSWORD = "adv_password"
    ADV_ADMIN_MGMT = "adv_admin_mgmt"
    ADV_FORCE_JOIN = "adv_force_join"
    ADV_REACTION = "adv_reaction"

    # Force Join Management
    FJ_ADD = "fj_add"
    FJ_REMOVE = "fj_remove"
    FJ_LIST = "fj_list"
    FJ_TOGGLE = "fj_toggle"

    # Reaction Lock Management
    RL_ADD = "rl_add"
    RL_REMOVE = "rl_remove"
    RL_LIST = "rl_list"

    # Broadcast Actions
    BROADCAST_TEXT = "broadcast_text"
    BROADCAST_MEDIA = "broadcast_media"
    BROADCAST_FORWARD = "broadcast_forward"
    BROADCAST_CANCEL = "broadcast_cancel"
    BROADCAST_CONFIRM = "broadcast_confirm"

    # File Management
    FILE_LIST = "file_list"
    FILE_SEARCH = "file_search"
    FILE_DELETE = "file_delete"
    FILE_DELETE_CONFIRM = "file_delete_confirm"

    # User Management
    USER_SEARCH = "user_search"
    USER_BAN = "user_ban"
    USER_UNBAN = "user_unban"
    USER_LIST = "user_list"

    # Admin Management
    ADMIN_ADD = "admin_add"
    ADMIN_REMOVE = "admin_remove"
    ADMIN_LIST = "admin_list"
    ADMIN_PERMS = "admin_perms"

    # User-side actions
    CHECK_JOIN = "check_join"
    CHECK_REACTION = "check_reaction"
    GET_FILE = "get_file"
    DOWNLOAD_FILE = "dl"

    # Pagination
    PAGE = "page"

    # Misc
    CONFIRM = "confirm"
    CANCEL = "cancel"


def _btn(text: str, callback_data: str) -> InlineKeyboardButton:
    """Shorthand to create an InlineKeyboardButton."""
    return InlineKeyboardButton(text=text, callback_data=callback_data)


# ═══════════════════════════════════════════════════════
# ADMIN PANEL KEYBOARDS
# ═══════════════════════════════════════════════════════


def admin_main_menu() -> InlineKeyboardMarkup:
    """Main admin panel keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("⚙️ تنظیمات کلی", CD.ADMIN_SETTINGS),
        _btn("📤 آپلود تکی", CD.ADMIN_UPLOAD_SINGLE),
    )
    builder.row(
        _btn("📦 آپلود گروهی", CD.ADMIN_UPLOAD_ALBUM),
        _btn("🔗 آپلود از لینک", CD.ADMIN_UPLOAD_LINK),
    )
    builder.row(
        _btn("📢 تبلیغ / ارسال همگانی", CD.ADMIN_BROADCAST),
        _btn("📊 آمار", CD.ADMIN_STATS),
    )
    builder.row(
        _btn("📝 تنظیم کپشن", CD.ADMIN_CAPTION),
        _btn("📝 تنظیم متون", CD.ADMIN_TEXTS),
    )
    builder.row(
        _btn("📁 مدیریت اشتراک فایل", CD.ADMIN_FILE_MGMT),
    )
    return builder.as_markup()


def admin_settings_menu() -> InlineKeyboardMarkup:
    """Settings sub-menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("👥 کاربران", CD.SETTINGS_USERS),
        _btn("📤 ارسال به کانال", CD.SETTINGS_CHANNEL),
    )
    builder.row(
        _btn("💬 گروه", CD.SETTINGS_GROUP),
        _btn("🔘 مدیریت دکمه‌ها", CD.SETTINGS_BUTTONS),
    )
    builder.row(
        _btn("📡 تنظیمات سین", CD.SETTINGS_SIN),
        _btn("📢 تنظیمات کانال", CD.SETTINGS_CHANNELS),
    )
    builder.row(
        _btn("🔒 تنظیم لینک اجباری", CD.SETTINGS_FORCE_JOIN),
        _btn("❌ لغو فوروارد / همگانی", CD.SETTINGS_CANCEL_FORWARD),
    )
    builder.row(
        _btn("🗂 مدیریت فایل", CD.SETTINGS_FILE_MGMT),
        _btn("⏩ فوروارد همگانی", CD.SETTINGS_FORWARD_ALL),
    )
    builder.row(
        _btn("📨 ارسال همگانی", CD.SETTINGS_SEND_ALL),
        _btn("🔴 خاموش و روشن", CD.SETTINGS_ON_OFF),
    )
    builder.row(
        _btn("👤 مدیریت کاربر", CD.SETTINGS_USER_MGMT),
    )
    builder.row(
        _btn("🔙 بازگشت", CD.ADMIN_PANEL),
    )
    return builder.as_markup()


def admin_advanced_settings() -> InlineKeyboardMarkup:
    """Advanced settings keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("⏩ فوروارد همگانی", CD.ADV_FORWARD),
        _btn("📨 ارسال همگانی", CD.ADV_SEND),
    )
    builder.row(
        _btn("🔴 خاموش و روشن", CD.ADV_ON_OFF),
        _btn("👤 مدیریت کاربر", CD.ADV_USER_MGMT),
    )
    builder.row(
        _btn("🗑 حذف فایل", CD.ADV_DELETE_FILE),
        _btn("⏱ تنظیمات تایمر", CD.ADV_TIMER),
    )
    builder.row(
        _btn("🔑 تنظیم پسورد", CD.ADV_PASSWORD),
        _btn("👑 مدیریت ادمین‌ها", CD.ADV_ADMIN_MGMT),
    )
    builder.row(
        _btn("🔒 قفل جوین اجباری", CD.ADV_FORCE_JOIN),
        _btn("❤️ قفل واکنش", CD.ADV_REACTION),
    )
    builder.row(
        _btn("🔙 بازگشت", CD.ADMIN_SETTINGS),
    )
    return builder.as_markup()


def admin_broadcast_menu() -> InlineKeyboardMarkup:
    """Broadcast options keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("📝 ارسال متن", CD.BROADCAST_TEXT),
        _btn("🖼 ارسال رسانه", CD.BROADCAST_MEDIA),
    )
    builder.row(
        _btn("⏩ فوروارد پیام", CD.BROADCAST_FORWARD),
    )
    builder.row(
        _btn("❌ لغو ارسال همگانی", CD.BROADCAST_CANCEL),
        _btn("🔙 بازگشت", CD.ADMIN_PANEL),
    )
    return builder.as_markup()


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirmation keyboard for broadcast."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("✅ تأیید و ارسال", CD.BROADCAST_CONFIRM),
        _btn("❌ لغو", CD.CANCEL),
    )
    return builder.as_markup()


def admin_stats_keyboard() -> InlineKeyboardMarkup:
    """Stats section keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("🔄 بروزرسانی", CD.ADMIN_STATS),
        _btn("🔙 بازگشت", CD.ADMIN_PANEL),
    )
    return builder.as_markup()


def admin_file_management() -> InlineKeyboardMarkup:
    """File management keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("📋 لیست فایل‌ها", CD.FILE_LIST),
        _btn("🔍 جستجوی فایل", CD.FILE_SEARCH),
    )
    builder.row(
        _btn("🗑 حذف فایل", CD.FILE_DELETE),
    )
    builder.row(
        _btn("🔙 بازگشت", CD.ADMIN_PANEL),
    )
    return builder.as_markup()


def admin_user_management() -> InlineKeyboardMarkup:
    """User management keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("🔍 جستجوی کاربر", CD.USER_SEARCH),
        _btn("📋 لیست کاربران", CD.USER_LIST),
    )
    builder.row(
        _btn("🚫 بن کاربر", CD.USER_BAN),
        _btn("✅ آنبن کاربر", CD.USER_UNBAN),
    )
    builder.row(
        _btn("🔙 بازگشت", CD.ADMIN_SETTINGS),
    )
    return builder.as_markup()


def admin_admin_management() -> InlineKeyboardMarkup:
    """Admin management keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("➕ افزودن ادمین", CD.ADMIN_ADD),
        _btn("➖ حذف ادمین", CD.ADMIN_REMOVE),
    )
    builder.row(
        _btn("📋 لیست ادمین‌ها", CD.ADMIN_LIST),
        _btn("🔑 تنظیم دسترسی‌ها", CD.ADMIN_PERMS),
    )
    builder.row(
        _btn("🔙 بازگشت", CD.ADV_ADMIN_MGMT),
    )
    return builder.as_markup()


def force_join_menu() -> InlineKeyboardMarkup:
    """Force join management keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("➕ افزودن کانال", CD.FJ_ADD),
        _btn("➖ حذف کانال", CD.FJ_REMOVE),
    )
    builder.row(
        _btn("📋 لیست کانال‌ها", CD.FJ_LIST),
        _btn("🔄 فعال/غیرفعال", CD.FJ_TOGGLE),
    )
    builder.row(
        _btn("🔙 بازگشت", CD.ADMIN_SETTINGS),
    )
    return builder.as_markup()


def reaction_lock_menu() -> InlineKeyboardMarkup:
    """Reaction lock management keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("➕ افزودن قفل واکنش", CD.RL_ADD),
        _btn("➖ حذف قفل واکنش", CD.RL_REMOVE),
    )
    builder.row(
        _btn("📋 لیست قفل‌ها", CD.RL_LIST),
    )
    builder.row(
        _btn("🔙 بازگشت", CD.ADMIN_SETTINGS),
    )
    return builder.as_markup()


def file_delete_confirm_keyboard(file_id: int) -> InlineKeyboardMarkup:
    """Confirmation for file deletion."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("✅ بله، حذف شود", f"{CD.FILE_DELETE_CONFIRM}:{file_id}"),
        _btn("❌ انصراف", CD.CANCEL),
    )
    return builder.as_markup()


def file_pagination_keyboard(
    current_page: int, total_pages: int, prefix: str = "files"
) -> InlineKeyboardMarkup:
    """Pagination keyboard for file lists."""
    builder = InlineKeyboardBuilder()
    buttons = []
    if current_page > 1:
        buttons.append(
            _btn("⬅️ قبلی", f"{CD.PAGE}:{prefix}:{current_page - 1}")
        )
    buttons.append(
        _btn(f"📄 {current_page}/{total_pages}", "noop")
    )
    if current_page < total_pages:
        buttons.append(
            _btn("➡️ بعدی", f"{CD.PAGE}:{prefix}:{current_page + 1}")
        )
    builder.row(*buttons)
    builder.row(_btn("🔙 بازگشت", CD.ADMIN_PANEL))
    return builder.as_markup()


# ═══════════════════════════════════════════════════════
# USER-SIDE KEYBOARDS
# ═══════════════════════════════════════════════════════


def force_join_check_keyboard(
    channels: list[dict],
) -> InlineKeyboardMarkup:
    """
    Keyboard for force join check.

    Args:
        channels: List of dicts with 'join_link' and 'display_name'.
    """
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.row(
            InlineKeyboardButton(
                text=f"📢 عضویت در {ch['display_name']}",
                url=ch["join_link"],
            )
        )
    builder.row(
        _btn("🔄 بررسی مجدد عضویت", CD.CHECK_JOIN),
    )
    return builder.as_markup()


def reaction_lock_check_keyboard(
    channel_id: int,
    message_id: int,
) -> InlineKeyboardMarkup:
    """Keyboard for reaction lock check."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❤️ رفتن به پست برای واکنش",
            url=f"https://t.me/c/{str(abs(channel_id))[4:]}/{message_id}",
        )
    )
    builder.row(
        _btn("🔄 بررسی مجدد واکنش", CD.CHECK_REACTION),
    )
    return builder.as_markup()


def file_download_keyboard(
    file_token: str,
    file_type: str = "document",
    extra_buttons: list[InlineKeyboardButton] | None = None,
) -> InlineKeyboardMarkup:
    """
    Keyboard for file download.

    Args:
        file_token: Deep link token for the file.
        file_type: Type of file (for icon).
        extra_buttons: Optional extra buttons.
    """
    icons = {
        "document": "📄",
        "photo": "🖼",
        "video": "🎬",
        "audio": "🎵",
        "voice": "🎤",
        "animation": "🎞",
    }
    icon = icons.get(file_type, "📥")

    builder = InlineKeyboardBuilder()
    builder.row(
        _btn(f"{icon} دریافت فایل", f"{CD.DOWNLOAD_FILE}:{file_token}")
    )
    if extra_buttons:
        builder.row(*extra_buttons)
    return builder.as_markup()


def get_file_keyboard(file_token: str) -> InlineKeyboardMarkup:
    """Simple keyboard with a single 'Get File' button."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("📥 دریافت فایل", f"{CD.GET_FILE}:{file_token}")
    )
    return builder.as_markup()


def on_off_keyboard(is_on: bool) -> InlineKeyboardMarkup:
    """Toggle keyboard for bot on/off."""
    builder = InlineKeyboardBuilder()
    if is_on:
        builder.row(
            _btn("🔴 خاموش کردن ربات", f"{CD.SETTINGS_ON_OFF}:off")
        )
    else:
        builder.row(
            _btn("🟢 روشن کردن ربات", f"{CD.SETTINGS_ON_OFF}:on")
        )
    builder.row(_btn("🔙 بازگشت", CD.ADMIN_SETTINGS))
    return builder.as_markup()


def confirm_cancel_keyboard(
    confirm_data: str, cancel_data: str = CD.CANCEL
) -> InlineKeyboardMarkup:
    """Generic confirm/cancel keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("✅ تأیید", confirm_data),
        _btn("❌ لغو", cancel_data),
    )
    return builder.as_markup()


def back_button(callback_data: str = CD.ADMIN_PANEL) -> InlineKeyboardMarkup:
    """Single back button keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(_btn("🔙 بازگشت", callback_data))
    return builder.as_markup()
