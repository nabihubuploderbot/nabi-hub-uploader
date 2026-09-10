"""کیبوردهای بخش فایل / Files keyboards."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def files_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 حذف فایل", callback_data="files:delete"),
                InlineKeyboardButton(text="🔒 تنظیم پسورد فایل", callback_data="files:password"),
            ],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="panel:general")],
        ]
    )


def cancel_keyboard(cb: str = "panel:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ لغو", callback_data=cb)]]
    )
