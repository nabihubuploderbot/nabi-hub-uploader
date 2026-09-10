"""کیبورد قفل‌ها / Lock keyboards (force join + reaction)."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.channel import Channel


def force_join_keyboard(channels: list[Channel], check_callback: str | None) -> InlineKeyboardMarkup:
    """دکمه‌های عضویت برای کانال‌های بلاک‌شده + دکمهٔ بررسی مجدد."""
    kb_rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for ch in channels:
        url = ch.invite_link
        if not url and ch.username:
            url = f"https://t.me/{ch.username}"
        row.append(
            InlineKeyboardButton(text=f"📢 {ch.title or ch.username or ch.chat_id}", url=url)
        )
        if len(row) == 2:
            kb_rows.append(row)
            row = []
    if row:
        kb_rows.append(row)

    if check_callback:
        kb_rows.append(
            [InlineKeyboardButton(text="🔄 بررسی مجدد", callback_data=check_callback)]
        )
    return InlineKeyboardMarkup(inline_keyboard=kb_rows)


def locks_menu_keyboard() -> InlineKeyboardMarkup:
    """منوی مدیریت قفل‌ها (ادمین)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ افزودن کانال", callback_data="locks:add"),
                InlineKeyboardButton(text="📋 لیست کانال‌ها", callback_data="locks:list"),
            ],
            [
                InlineKeyboardButton(text="🔓 روشن/خاموش جوین اجباری", callback_data="locks:toggle_join"),
            ],
            [
                InlineKeyboardButton(text="👍 تنظیم قفل واکنش", callback_data="locks:reaction"),
                InlineKeyboardButton(text="⛔ غیرفعال‌کردن قفل واکنش", callback_data="locks:reaction_off"),
            ],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="panel:advanced")],
        ]
    )


def channels_list_keyboard(channels: list) -> InlineKeyboardMarkup:
    """لیست کانال‌ها با دکمهٔ حذف هرکدام."""
    rows = [
        [
            InlineKeyboardButton(
                text=f"❌ {ch.title or ch.username or ch.chat_id}",
                callback_data=f"locks:del:{ch.id}",
            )
        ]
        for ch in channels
    ]
    rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="locks:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
