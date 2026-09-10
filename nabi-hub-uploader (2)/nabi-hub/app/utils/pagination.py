"""کمک‌کننده‌های دکمه / Small button helpers."""
from aiogram.types import InlineKeyboardButton


def inline_pagination(callback_data: str, text: str, url: str | None = None) -> InlineKeyboardButton:
    """ساخت دکمهٔ بازگشت/صفحه‌بندی."""
    if url:
        return InlineKeyboardButton(text=text, url=url)
    return InlineKeyboardButton(text=text, callback_data=callback_data)
