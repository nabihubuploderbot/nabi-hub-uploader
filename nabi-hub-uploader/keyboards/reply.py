"""
keyboards/reply.py — Reply Keyboard Markups.

Used for multi-step processes where inline keyboards aren't suitable.
"""

from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def admin_reply_menu() -> ReplyKeyboardMarkup:
    """Admin reply keyboard with main actions."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📋 پنل مدیریت"),
        KeyboardButton(text="📊 آمار"),
    )
    builder.row(
        KeyboardButton(text="📤 آپلود فایل"),
        KeyboardButton(text="📦 آپلود آلبوم"),
    )
    builder.row(
        KeyboardButton(text="❌ لغو"),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Simple cancel button."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ لغو"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def done_keyboard() -> ReplyKeyboardMarkup:
    """Done button for album upload."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="✅ اتمام آپلود"),
        KeyboardButton(text="❌ لغو"),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove reply keyboard."""
    return ReplyKeyboardRemove()
