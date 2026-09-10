"""کیبوردهای متن و کاربران / Texts & users keyboards."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def texts_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 متن استارت", callback_data="texts:start"),
                InlineKeyboardButton(text="🔒 متن قفل", callback_data="texts:lock"),
            ],
            [
                InlineKeyboardButton(text="✍️ کپشن پیش‌فرض", callback_data="texts:caption"),
            ],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="panel:main")],
        ]
    )


def users_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⛔ مسدودسازی", callback_data="users:ban"),
                InlineKeyboardButton(text="✅ رفع مسدودی", callback_data="users:unban"),
            ],
            [
                InlineKeyboardButton(text="📋 آخرین کاربران", callback_data="users:list"),
            ],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="panel:general")],
        ]
    )


def admins_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ افزودن ادمین", callback_data="admins:add"),
                InlineKeyboardButton(text="➖ حذف ادمین", callback_data="admins:remove"),
            ],
            [
                InlineKeyboardButton(text="📋 لیست ادمین‌ها", callback_data="admins:list"),
            ],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="panel:advanced")],
        ]
    )
