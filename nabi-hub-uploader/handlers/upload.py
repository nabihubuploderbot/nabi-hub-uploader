"""
handlers/upload.py — File upload handlers.

Handles single file uploads, album uploads, and link uploads.
Uses FSM for multi-step processes.
"""

from __future__ import annotations

import uuid
from typing import Callable

from aiogram import Router, F, Bot
from aiogram.types import Message, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings
from services.file_service import FileService
from services.setting_service import SettingService
from utils.telegram import (
    get_file_type,
    get_file_id_and_unique_id,
    get_file_size,
    get_file_name,
    get_mime_type,
)
from keyboards.reply import (
    cancel_keyboard,
    done_keyboard,
    remove_keyboard,
    admin_reply_menu,
)
from keyboards.inline import admin_main_menu, CD


router = Router(name="upload")


# ── FSM States ──────────────────────────────────────


class UploadStates(StatesGroup):
    """FSM states for file upload process."""
    waiting_single_file = State()
    waiting_album_files = State()
    waiting_album_caption = State()
    waiting_single_caption = State()
    waiting_link = State()
    waiting_link_caption = State()


# ═══════════════════════════════════════════════════════
# SINGLE FILE UPLOAD
# ═══════════════════════════════════════════════════════


@router.message(F.text == "📤 آپلود فایل")
async def start_single_upload(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Start single file upload process."""
    if not is_admin:
        return

    await state.set_state(UploadStates.waiting_single_file)
    await message.answer(
        t("upload_start"),
        reply_markup=cancel_keyboard(),
    )


@router.message(UploadStates.waiting_single_file, F.content_type.in_({
    ContentType.DOCUMENT,
    ContentType.PHOTO,
    ContentType.VIDEO,
    ContentType.AUDIO,
    ContentType.VOICE,
    ContentType.VIDEO_NOTE,
    ContentType.ANIMATION,
}))
async def process_single_file(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Process a single file upload."""
    file_type = get_file_type(message)
    file_id, file_unique_id = get_file_id_and_unique_id(message)

    if not file_type or not file_id or not file_unique_id:
        await message.answer(t("error_occurred"))
        return

    # Get caption from message
    caption = message.caption or ""

    # Create file record
    file_record = await FileService.create_file(
        session=session,
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_type=file_type,
        uploader_id=message.from_user.id,
        file_name=get_file_name(message),
        file_size=get_file_size(message),
        mime_type=get_mime_type(message),
        caption=caption,
    )

    # Generate deep link
    from config import settings as cfg
    bot_username = (await message.bot.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start={file_record.deep_link_token}"

    await state.clear()

    await message.answer(
        f"✅ فایل با موفقیت آپلود شد!\n\n"
        f"📄 نوع: {file_type}\n"
        f"📦 حجم: {file_record.human_size}\n"
        f"🔗 لینک عمیق:\n`{deep_link}`\n\n"
        f"لینک بالا را کپی کنید و به اشتراک بگذارید.",
        parse_mode="Markdown",
        reply_markup=admin_reply_menu(),
    )

    logger.info(
        f"Single file uploaded: id={file_record.id} "
        f"type={file_type} by admin={message.from_user.id}"
    )


@router.message(UploadStates.waiting_single_file, F.text == "❌ لغو")
async def cancel_single_upload(
    message: Message,
    state: FSMContext,
    t: Callable[[str], str],
) -> None:
    """Cancel single file upload."""
    await state.clear()
    await message.answer(
        t("upload_cancelled"),
        reply_markup=admin_reply_menu(),
    )


# ═══════════════════════════════════════════════════════
# ALBUM / BULK UPLOAD
# ═══════════════════════════════════════════════════════


@router.message(F.text == "📦 آپلود آلبوم")
async def start_album_upload(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Start album/bulk upload process."""
    if not is_admin:
        return

    album_id = FileService.generate_album_id()
    await state.set_state(UploadStates.waiting_album_files)
    await state.update_data(album_id=album_id, files=[])
    await message.answer(
        t("upload_album_start"),
        reply_markup=done_keyboard(),
    )


@router.message(UploadStates.waiting_album_files, F.content_type.in_({
    ContentType.DOCUMENT,
    ContentType.PHOTO,
    ContentType.VIDEO,
    ContentType.AUDIO,
    ContentType.VOICE,
    ContentType.VIDEO_NOTE,
    ContentType.ANIMATION,
}))
async def process_album_file(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Process each file in album upload."""
    data = await state.get_data()
    album_id = data.get("album_id")
    files_list = data.get("files", [])

    file_type = get_file_type(message)
    file_id, file_unique_id = get_file_id_and_unique_id(message)

    if not file_type or not file_id or not file_unique_id:
        await message.answer(t("error_occurred"))
        return

    # Create file record
    file_record = await FileService.create_file(
        session=session,
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_type=file_type,
        uploader_id=message.from_user.id,
        file_name=get_file_name(message),
        file_size=get_file_size(message),
        mime_type=get_mime_type(message),
        caption=message.caption or "",
        album_id=album_id,
        album_index=len(files_list),
    )

    files_list.append(file_record.id)
    await state.update_data(files=files_list)

    count = len(files_list)
    await message.answer(
        t("album_files_received", count=count),
        reply_markup=done_keyboard(),
    )


@router.message(UploadStates.waiting_album_files, F.text.in_({"✅ اتمام آپلود", "✅ Done"}))
async def finish_album_upload(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Finish album upload and ask for album caption."""
    data = await state.get_data()
    files_count = len(data.get("files", []))

    if files_count == 0:
        await state.clear()
        await message.answer("⚠️ هیچ فایلی آپلود نشد!", reply_markup=admin_reply_menu())
        return

    await state.set_state(UploadStates.waiting_album_caption)
    await message.answer(
        f"📦 تعداد فایل‌ها: {files_count}\n\n"
        "📝 لطفاً کپشن آلبوم را ارسال کنید (یا /skip برای رد شدن):",
        reply_markup=remove_keyboard(),
    )


@router.message(UploadStates.waiting_album_caption)
async def set_album_caption(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Set album caption and finalize."""
    data = await state.get_data()
    album_id = data.get("album_id")
    files = data.get("files", [])

    caption = None
    if message.text and message.text != "/skip":
        caption = message.text

    # Update all files in the album with the shared caption
    if caption and album_id:
        from sqlalchemy import update
        from models.file import UploadedFile
        stmt = (
            update(UploadedFile)
            .where(UploadedFile.album_id == album_id)
            .values(album_caption=caption, caption=caption)
        )
        await session.execute(stmt)
        await session.commit()

    # Generate deep link for the album (use first file's token)
    first_file = await FileService.get_by_id(session, files[0]) if files else None
    if first_file:
        bot_username = (await message.bot.get_me()).username
        deep_link = f"https://t.me/{bot_username}?start={first_file.deep_link_token}"
    else:
        deep_link = "N/A"

    await state.clear()

    await message.answer(
        t("upload_done", count=len(files)) + f"\n\n🔗 لینک عمیق:\n`{deep_link}`",
        parse_mode="Markdown",
        reply_markup=admin_reply_menu(),
    )

    logger.info(
        f"Album uploaded: album_id={album_id} files={len(files)} "
        f"by admin={message.from_user.id}"
    )


@router.message(UploadStates.waiting_album_files, F.text == "❌ لغو")
async def cancel_album_upload(
    message: Message,
    state: FSMContext,
    t: Callable[[str], str],
) -> None:
    """Cancel album upload."""
    await state.clear()
    await message.answer(t("upload_cancelled"), reply_markup=admin_reply_menu())


# ═══════════════════════════════════════════════════════
# UPLOAD FROM LINK
# ═══════════════════════════════════════════════════════


@router.message(F.text == "🔗 آپلود از لینک")
async def start_link_upload(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Start upload from direct link process."""
    if not is_admin:
        return

    await state.set_state(UploadStates.waiting_link)
    await message.answer(
        t("upload_link_prompt"),
        reply_markup=cancel_keyboard(),
    )


@router.message(UploadStates.waiting_link, F.text.startswith("http"))
async def process_link_upload(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Process direct link upload."""
    url = message.text.strip()

    if not url.startswith(("http://", "https://")):
        await message.answer("⚠️ لطفاً یک لینک معتبر HTTP/HTTPS ارسال کنید.")
        return

    await state.update_data(link_url=url)
    await state.set_state(UploadStates.waiting_link_caption)

    await message.answer(
        "📝 لطفاً کپشن فایل را ارسال کنید (یا /skip برای رد شدن):",
        reply_markup=remove_keyboard(),
    )


@router.message(UploadStates.waiting_link_caption)
async def set_link_caption(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
    bot: Bot,
) -> None:
    """Set caption for link upload and process."""
    data = await state.get_data()
    url = data.get("link_url", "")

    caption = None
    if message.text and message.text != "/skip":
        caption = message.text

    # Try to download and re-upload the file
    try:
        import aiohttp
        async with aiohttp.ClientSession() as http_session:
            async with http_session.get(url) as resp:
                if resp.status != 200:
                    await message.answer(f"⚠️ خطا در دانلود فایل: HTTP {resp.status}")
                    await state.clear()
                    return

                content_type = resp.headers.get("Content-Type", "")
                content_length = int(resp.headers.get("Content-Length", 0))

                # Read file data
                file_data = await resp.read()

                # Determine file name from URL
                from urllib.parse import urlparse
                parsed = urlparse(url)
                file_name = parsed.path.split("/")[-1] or "file"

                # Send as document
                from aiogram.types import BufferedInputFile
                input_file = BufferedInputFile(file_data, filename=file_name)

                sent_msg = await message.answer_document(
                    document=input_file,
                    caption=caption or "",
                    parse_mode="HTML",
                )

                # Save to database
                if sent_msg.document:
                    await FileService.create_file(
                        session=session,
                        file_id=sent_msg.document.file_id,
                        file_unique_id=sent_msg.document.file_unique_id,
                        file_type="document",
                        uploader_id=message.from_user.id,
                        file_name=file_name,
                        file_size=len(file_data),
                        caption=caption,
                    )

                await message.answer("✅ فایل از لینک آپلود شد!")
                logger.info(f"File uploaded from link: {url} by admin={message.from_user.id}")

    except Exception as e:
        logger.error(f"Failed to upload from link: {e}")
        await message.answer(f"⚠️ خطا در آپلود: {str(e)}")

    await state.clear()
    await message.answer("عملیات تکمیل شد.", reply_markup=admin_reply_menu())


@router.message(UploadStates.waiting_link, F.text == "❌ لغو")
async def cancel_link_upload(
    message: Message,
    state: FSMContext,
    t: Callable[[str], str],
) -> None:
    """Cancel link upload."""
    await state.clear()
    await message.answer(t("upload_cancelled"), reply_markup=admin_reply_menu())

# ═══════════════════════════════════════════════════════
# INLINE PANEL UPLOAD BUTTONS → FSM ENTRY POINTS
# These handlers were missing — the admin panel buttons
# (آپلود تکی / گروهی / از لینک) sent callbacks that no
# handler matched, so they silently did nothing.
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADMIN_UPLOAD_SINGLE)
async def cb_start_single_upload(
    callback: CallbackQuery,
    state: FSMContext,
    t: Callable[[str], str],
    is_admin: bool,
) -> None:
    """Start single file upload from the inline admin panel."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await state.set_state(UploadStates.waiting_single_file)
    await callback.message.answer(
        t("upload_start"),
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_UPLOAD_ALBUM)
async def cb_start_album_upload(
    callback: CallbackQuery,
    state: FSMContext,
    t: Callable[[str], str],
    is_admin: bool,
) -> None:
    """Start album/bulk upload from the inline admin panel."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    album_id = FileService.generate_album_id()
    await state.set_state(UploadStates.waiting_album_files)
    await state.update_data(album_id=album_id, files=[])
    await callback.message.answer(
        t("upload_album_start"),
        reply_markup=done_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == CD.ADMIN_UPLOAD_LINK)
async def cb_start_link_upload(
    callback: CallbackQuery,
    state: FSMContext,
    t: Callable[[str], str],
    is_admin: bool,
) -> None:
    """Start link upload from the inline admin panel."""
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return

    await state.set_state(UploadStates.waiting_link)
    await callback.message.answer(
        t("upload_link_prompt"),
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()

