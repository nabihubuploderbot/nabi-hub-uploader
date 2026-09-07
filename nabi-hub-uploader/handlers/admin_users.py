"""
handlers/admin_users.py — User management handlers.

Handles user listing, searching, banning, and unbanning.
"""

from __future__ import annotations

from typing import Callable

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from services.user_service import UserService
from keyboards.inline import (
    CD,
    admin_user_management,
    back_button,
)
from keyboards.reply import admin_reply_menu, remove_keyboard

router = Router(name="admin_users")


class UserStates(StatesGroup):
    """FSM states for user management."""
    waiting_search = State()
    waiting_ban_id = State()
    waiting_unban_id = State()


# ═══════════════════════════════════════════════════════
# USER LIST
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.USER_LIST)
async def show_user_list(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show recent users."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    users = await UserService.get_all(session)
    total = len(users)

    text = f"👥 **آخرین کاربران** (کل: {total:,})\n\n"

    for user in users[:20]:
        ban_icon = "🚫" if user.is_banned else "✅"
        text += (
            f"{ban_icon} `{user.user_id}` | "
            f"@{user.username or 'N/A'} | "
            f"{user.full_name}\n"
            f"   ⬇️ {user.download_count} | "
            f"📅 {user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A'}\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.SETTINGS_USER_MGMT),
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# USER SEARCH
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.USER_SEARCH)
async def start_user_search(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """Start user search."""
    if not is_admin:
        return

    await state.set_state(UserStates.waiting_search)
    await callback.message.edit_text(
        "🔍 لطفاً آیدی عددی یا نام کاربری مورد نظر را وارد کنید:",
    )
    await callback.answer()


@router.message(UserStates.waiting_search)
async def process_user_search(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Process user search query."""
    query = message.text.strip()
    await state.clear()

    users = await UserService.search_user(session, query)

    if not users:
        await message.answer("⚠️ کاربری یافت نشد.", reply_markup=admin_reply_menu())
        return

    text = f"🔍 **نتایج جستجو:**\n\n"
    for user in users[:10]:
        ban_icon = "🚫" if user.is_banned else "✅"
        text += (
            f"{ban_icon} `{user.user_id}` | @{user.username or 'N/A'}\n"
            f"   👤 {user.full_name}\n"
            f"   ⬇️ دانلودها: {user.download_count}\n"
            f"   📅 عضویت: {user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A'}\n\n"
        )

    await message.answer(text, parse_mode="Markdown", reply_markup=admin_reply_menu())


# ═══════════════════════════════════════════════════════
# BAN USER
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.USER_BAN)
async def start_ban_user(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """Start ban user process."""
    if not is_admin:
        return

    await state.set_state(UserStates.waiting_ban_id)
    await callback.message.edit_text(
        "🚫 لطفاً آیدی عددی کاربر مورد نظر برای بن را وارد کنید:",
    )
    await callback.answer()


@router.message(UserStates.waiting_ban_id)
async def process_ban_user(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Process ban user request."""
    try:
        user_id = int(message.text.strip())
        banned = await UserService.ban_user(session, user_id)
        await state.clear()

        if banned:
            await message.answer(
                t("user_banned", user_id=user_id),
                reply_markup=admin_reply_menu(),
            )
        else:
            await message.answer(
                "⚠️ کاربر یافت نشد.",
                reply_markup=admin_reply_menu(),
            )
    except ValueError:
        await message.answer("⚠️ آیدی نامعتبر.")


# ═══════════════════════════════════════════════════════
# UNBAN USER
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.USER_UNBAN)
async def start_unban_user(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """Start unban user process."""
    if not is_admin:
        return

    await state.set_state(UserStates.waiting_unban_id)
    await callback.message.edit_text(
        "✅ لطفاً آیدی عددی کاربر مورد نظر برای آنبن را وارد کنید:",
    )
    await callback.answer()


@router.message(UserStates.waiting_unban_id)
async def process_unban_user(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Process unban user request."""
    try:
        user_id = int(message.text.strip())
        unbanned = await UserService.unban_user(session, user_id)
        await state.clear()

        if unbanned:
            await message.answer(
                t("user_unbanned", user_id=user_id),
                reply_markup=admin_reply_menu(),
            )
        else:
            await message.answer(
                "⚠️ کاربر یافت نشد.",
                reply_markup=admin_reply_menu(),
            )
    except ValueError:
        await message.answer("⚠️ آیدی نامعتبر.")
