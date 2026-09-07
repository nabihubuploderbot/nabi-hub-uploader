"""
handlers/admin_files.py — File management handlers.

Handles file listing, searching, and deletion.
"""

from __future__ import annotations

from typing import Callable

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from services.file_service import FileService
from keyboards.inline import (
    CD,
    admin_file_management,
    file_delete_confirm_keyboard,
    file_pagination_keyboard,
    back_button,
)
from keyboards.reply import admin_reply_menu, remove_keyboard

router = Router(name="admin_files")

FILES_PER_PAGE = 5


class FileStates(StatesGroup):
    """FSM states for file management."""
    waiting_search_query = State()
    waiting_delete_token = State()


# ═══════════════════════════════════════════════════════
# FILE LIST
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.FILE_LIST)
async def show_file_list(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Show paginated file list."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await _show_files_page(callback, session, page=1)


@router.callback_query(F.data.startswith(f"{CD.PAGE}:files:"))
async def paginate_files(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Handle file list pagination."""
    if not is_admin:
        return

    page = int(callback.data.split(":")[2])
    await _show_files_page(callback, session, page=page)


async def _show_files_page(
    callback: CallbackQuery,
    session: AsyncSession,
    page: int = 1,
) -> None:
    """Display a page of files."""
    total_files = await FileService.count_files(session)
    total_pages = max(1, (total_files + FILES_PER_PAGE - 1) // FILES_PER_PAGE)
    page = min(page, total_pages)

    offset = (page - 1) * FILES_PER_PAGE
    files = await FileService.get_all_files(session, limit=FILES_PER_PAGE, offset=offset)

    if not files:
        await callback.message.edit_text(
            "📁 هیچ فایلی یافت نشد.",
            reply_markup=back_button(CD.ADMIN_FILE_MGMT),
        )
        await callback.answer()
        return

    text = f"📁 **لیست فایل‌ها** (صفحه {page}/{total_pages})\n\n"

    icons = {
        "document": "📄", "photo": "🖼", "video": "🎬",
        "audio": "🎵", "voice": "🎤", "animation": "🎞",
    }

    for f in files:
        icon = icons.get(f.file_type, "📦")
        text += (
            f"{icon} `ID:{f.id}` | {f.file_name or 'بدون نام'}\n"
            f"   📦 {f.human_size} | ⬇️ {f.download_count} | 🔗 `{f.deep_link_token}`\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=file_pagination_keyboard(page, total_pages, "files"),
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
# FILE SEARCH
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.FILE_SEARCH)
async def start_file_search(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """Start file search."""
    if not is_admin:
        return

    await state.set_state(FileStates.waiting_search_query)
    await callback.message.edit_text(
        "🔍 لطفاً عبارت جستجو را وارد کنید:\n\n"
        "(نام فایل یا توکن)",
    )
    await callback.answer()


@router.message(FileStates.waiting_search_query)
async def process_file_search(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Process file search query."""
    query = message.text.strip()
    await state.clear()

    files = await FileService.search_files(session, query)

    if not files:
        await message.answer(
            f"🔍 نتیجه‌ای برای «{query}» یافت نشد.",
            reply_markup=admin_reply_menu(),
        )
        return

    icons = {
        "document": "📄", "photo": "🖼", "video": "🎬",
        "audio": "🎵", "voice": "🎤", "animation": "🎞",
    }

    text = f"🔍 **نتایج جستجو برای «{query}»:**\n\n"
    for f in files[:20]:  # Limit to 20 results
        icon = icons.get(f.file_type, "📦")
        text += (
            f"{icon} `ID:{f.id}` | {f.file_name or 'بدون نام'}\n"
            f"   📦 {f.human_size} | 🔗 `{f.deep_link_token}`\n\n"
        )

    await message.answer(text, parse_mode="Markdown", reply_markup=admin_reply_menu())


# ═══════════════════════════════════════════════════════
# FILE DELETE
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.FILE_DELETE)
async def start_file_delete(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
) -> None:
    """Start file deletion process."""
    if not is_admin:
        return

    await state.set_state(FileStates.waiting_delete_token)
    await callback.message.edit_text(
        "🗑 لطفاً آیدی فایل مورد نظر برای حذف را وارد کنید:\n\n"
        "(آیدی عددی فایل از لیست فایل‌ها)",
    )
    await callback.answer()


@router.message(FileStates.waiting_delete_token)
async def process_file_delete(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Process file deletion request."""
    try:
        file_id = int(message.text.strip())
        file_record = await FileService.get_by_id(session, file_id)

        if not file_record:
            await message.answer("⚠️ فایل یافت نشد.")
            await state.clear()
            return

        icons = {
            "document": "📄", "photo": "🖼", "video": "🎬",
            "audio": "🎵", "voice": "🎤", "animation": "🎞",
        }
        icon = icons.get(file_record.file_type, "📦")

        await state.update_data(delete_file_id=file_id)
        await state.set_state(FileStates.waiting_delete_token)  # Reuse state for confirmation

        await message.answer(
            f"🗑 **تأیید حذف فایل:**\n\n"
            f"{icon} `ID:{file_record.id}`\n"
            f"📄 نام: {file_record.file_name or 'بدون نام'}\n"
            f"📦 حجم: {file_record.human_size}\n"
            f"⬇️ دانلودها: {file_record.download_count}\n\n"
            f"آیا مطمئن هستید؟",
            reply_markup=file_delete_confirm_keyboard(file_id),
            parse_mode="Markdown",
        )

    except ValueError:
        await message.answer("⚠️ آیدی نامعتبر.")


@router.callback_query(F.data.startswith(f"{CD.FILE_DELETE_CONFIRM}:"))
async def confirm_file_delete(
    callback: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Confirm file deletion."""
    if not is_admin:
        return

    file_id = int(callback.data.split(":")[1])
    deleted = await FileService.delete_file(session, file_id)

    if deleted:
        await callback.message.edit_text(f"🗑 فایل `ID:{file_id}` حذف شد.", parse_mode="Markdown")
    else:
        await callback.message.edit_text("⚠️ فایل یافت نشد یا قبلاً حذف شده است.")

    await callback.answer()
