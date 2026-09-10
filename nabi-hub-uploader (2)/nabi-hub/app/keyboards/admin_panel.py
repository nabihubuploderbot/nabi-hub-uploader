"""کیبورد پنل ادمین / Admin panel inline keyboards."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.utils.pagination import inline_pagination


def main_panel_keyboard() -> InlineKeyboardMarkup:
    """منوی اصلی ادمین (مطابق منوی درخواستی)."""
    rows = [
        [
            InlineKeyboardButton(text="⚙️ تنظیمات کلی", callback_data="panel:general"),
            InlineKeyboardButton(text="🔧 تنظیمات پیشرفته", callback_data="panel:advanced"),
        ],
        [
            InlineKeyboardButton(text="📤 آپلود تکی", callback_data="upload:single"),
            InlineKeyboardButton(text="🗂 آپلود گروهی", callback_data="upload:album"),
        ],
        [
            InlineKeyboardButton(text="🔗 آپلود از لینک", callback_data="upload:link"),
        ],
        [
            InlineKeyboardButton(text="📣 تبلیغ / ارسال همگانی", callback_data="broadcast:start"),
        ],
        [
            InlineKeyboardButton(text="📊 آمار", callback_data="stats:show"),
            InlineKeyboardButton(text="✍️ تنظیم کپشن", callback_data="texts:caption"),
        ],
        [
            InlineKeyboardButton(text="📝 تنظیم متون", callback_data="texts:menu"),
            InlineKeyboardButton(text="🔒 مدیریت اشتراک فایل", callback_data="files:manage"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def general_settings_keyboard() -> InlineKeyboardMarkup:
    """منوی تنظیمات کلی."""
    rows = [
        [
            InlineKeyboardButton(text="👥 کاربران", callback_data="users:menu"),
            InlineKeyboardButton(text="📤 ارسال به کانال", callback_data="settings:toggle_channel"),
        ],
        [
            InlineKeyboardButton(text="👥 گروه", callback_data="settings:group"),
            InlineKeyboardButton(text="🔘 مدیریت دکمه‌ها", callback_data="settings:buttons"),
        ],
        [
            InlineKeyboardButton(text="⚙️ تنظیمات سین", callback_data="settings:sin"),
            InlineKeyboardButton(text="📡 تنظیمات کانال", callback_data="settings:log_channel"),
        ],
        [
            InlineKeyboardButton(text="🔒 تنظیم لینک اجباری", callback_data="locks:menu"),
        ],
        [
            InlineKeyboardButton(text="🚫 لغو فوروارد/همگانی", callback_data="broadcast:cancel_all"),
            InlineKeyboardButton(text="📁 مدیریت فایل", callback_data="files:manage"),
        ],
        [
            InlineKeyboardButton(text="↗️ فوروارد همگانی", callback_data="broadcast:forward"),
            InlineKeyboardButton(text="📣 ارسال همگانی", callback_data="broadcast:start"),
        ],
        [
            InlineKeyboardButton(text="🟢 خاموش/روشن", callback_data="settings:power"),
        ],
        [inline_pagination("panel:main", "🔙 بازگشت")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def advanced_settings_keyboard() -> InlineKeyboardMarkup:
    """منوی تنظیمات پیشرفته."""
    rows = [
        [
            InlineKeyboardButton(text="↗️ فوروارد همگانی", callback_data="broadcast:forward"),
            InlineKeyboardButton(text="📣 ارسال همگانی", callback_data="broadcast:start"),
        ],
        [
            InlineKeyboardButton(text="🟢 خاموش و روشن", callback_data="settings:power"),
            InlineKeyboardButton(text="👤 مدیریت کاربر", callback_data="users:menu"),
        ],
        [
            InlineKeyboardButton(text="🗑 حذف فایل", callback_data="files:delete"),
            InlineKeyboardButton(text="⏱ تنظیم تایمر", callback_data="settings:timer"),
        ],
        [
            InlineKeyboardButton(text="🔑 تنظیم پسورد", callback_data="settings:password"),
            InlineKeyboardButton(text="👑 مدیریت ادمین‌ها", callback_data="admins:menu"),
        ],
        [
            InlineKeyboardButton(text="🔒 قفل جوین اجباری", callback_data="locks:menu"),
            InlineKeyboardButton(text="👍 قفل واکنش", callback_data="locks:reaction"),
        ],
        [inline_pagination("panel:main", "🔙 بازگشت")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard(yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ بله", callback_data=yes_cb),
                InlineKeyboardButton(text="❌ خیر", callback_data=no_cb),
            ]
        ]
    )
