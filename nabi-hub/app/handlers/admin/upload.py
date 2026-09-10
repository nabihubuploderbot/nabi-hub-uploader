from app.states import UploadStates

"""آپلود ادمین (تکی/آلبوم/لینک) / Admin upload handlers (single/album/link)."""
import asyncio

import aiohttp
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from loguru import logger

from app.core.db import Database
from app.locales.fa import TEXTS
from app.services.file_service import FileService
from app.utils.helpers import extract_file, file_type_of, human_size

router = Router(name="admin_upload")

# بافر آلبوم: media_group_id → data / Album buffer per media_group
_album_buffer: dict[str, dict] = {}
ALBUM_WAIT_SECONDS = 2.0

MAX_BOT_FILE_SIZE = 20 * 1024 * 1024  # محدودیت دانلود Bot API


async def _save_and_report(
    message: Message,
    db: Database,
    *,
    telegram_file_id: str,
    ftype: str,
    size: int,
    name: str | None,
    caption: str | None,
    album_id: int | None = None,
) -> None:
    """ذخیرهٔ فایل در دیتابیس و گزارش لینک / Save file to DB & report link."""
    async with db.session_factory() as session:
        svc = FileService(session)
        file = await svc.create_file(
            telegram_file_id=telegram_file_id,
            file_type=ftype,
            file_size=size,
            file_name=name,
            caption=caption,
            album_id=album_id,
            owner_id=message.from_user.id,
        )
    me = await message.bot.me()
    link = f"https://t.me/{me.username}?start={file.file_code}"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔗 اشتراک‌گذاری", url=link)]]
    )
    await message.answer(
        f"✅ فایل ثبت شد!\n\n🆔 کد: <code>{file.file_code}</code>\n"
        f"💾 حجم: {human_size(size)}\n🔗 لینک: <code>{link}</code>",
        reply_markup=kb,
    )


# ── آپلود تکی / Single upload ──
@router.callback_query(F.data == "upload:single")
async def cb_upload_single(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UploadStates.waiting_file)
    await cb.message.answer(TEXTS["send_file"])
    await cb.answer()


@router.message(UploadStates.waiting_file)
async def msg_upload_single(message: Message, state: FSMContext, db: Database) -> None:
    """دریافت فایل تکی / Receive single file."""
    file_id, size, name = extract_file(message)
    if file_id is None:
        await message.answer(TEXTS["send_file"])
        return
    await state.clear()
    ftype = file_type_of(message)
    caption = message.html_text if message.caption else None
    await _save_and_report(
        message, db,
        telegram_file_id=file_id, ftype=ftype, size=size,
        name=name, caption=caption,
    )


# ── آپلود گروهی (آلبوم) / Album upload ──
@router.callback_query(F.data == "upload:album")
async def cb_upload_album(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UploadStates.waiting_album)
    await cb.message.answer(TEXTS["send_album"])
    await cb.answer()


@router.message(UploadStates.waiting_album, Command("done"))
async def msg_album_done(message: Message, state: FSMContext) -> None:
    """دستور /done برای اطمینان از پایان آلبوم / /done to finalize album."""
    await state.clear()
    await message.answer("✅ حالت آلبوم بسته شد. (آلبوم‌های ارسال‌شده خودکار ثبت می‌شوند)")


@router.message(UploadStates.waiting_album)
async def msg_upload_album(message: Message, state: FSMContext, db: Database) -> None:
    """دریافت فایل‌های آلبوم با بافر media_group / Receive album files with media_group buffer."""
    group_id = message.media_group_id or f"solo-{message.message_id}"

    file_id, size, name = extract_file(message)
    if file_id is None:
        return

    caption = message.html_text if message.caption else None
    buffer = _album_buffer.setdefault(
        group_id, {"files": [], "task": None, "owner": message.from_user.id}
    )
    buffer["files"].append({
        "file_id": file_id,
        "ftype": file_type_of(message),
        "size": size,
        "name": name,
        "caption": caption,
    })

    async def _flush() -> None:
        """بعد از سکوت، آلبوم را ثبت کن / Flush album after silence."""
        await asyncio.sleep(ALBUM_WAIT_SECONDS)
        data = _album_buffer.pop(group_id, None)
        if not data:
            return
        files = data["files"]
        async with db.session_factory() as session:
            svc = FileService(session)
            album = await svc.create_album(
                title=f"آلبوم {len(files)} فایلی",
                caption=next((f["caption"] for f in files if f["caption"]), None),
                owner_id=data["owner"],
            )
            from app.models.file import File
            from app.utils.helpers import generate_code

            for f in files:
                session.add(File(
                    file_code=generate_code(),
                    telegram_file_id=f["file_id"],
                    file_type=f["ftype"],
                    file_size=f["size"],
                    file_name=f["name"],
                    caption=f["caption"],
                    album_id=album.id,
                    owner_id=data["owner"],
                ))
            await session.commit()

        username = (await message.bot.me()).username
        await message.answer(
            f"✅ آلبوم با <b>{len(files)}</b> فایل ثبت شد!\n\n"
            f"🔗 لینک: <code>https://t.me/{username}?start={album.album_code}</code>"
        )

    if buffer["task"]:
        buffer["task"].cancel()
    buffer["task"] = asyncio.create_task(_flush())


# ── آپلود از لینک / Upload from direct URL ──
@router.callback_query(F.data == "upload:link")
async def cb_upload_link(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UploadStates.waiting_link)
    await cb.message.answer(TEXTS["send_link"])
    await cb.answer()


@router.message(UploadStates.waiting_link, F.text.regexp(r"^https?://\S+$"))
async def msg_upload_link(message: Message, state: FSMContext, db: Database) -> None:
    """دانلود از لینک مستقیم و ارسال به تلگرام / Download from URL & upload to Telegram."""
    url = (message.text or "").strip()
    await message.answer("⏳ در حال دانلود از لینک ...")

    try:
        async with aiohttp.ClientSession() as http:
            async with http.get(url, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status != 200:
                    await message.answer(TEXTS["invalid_link"])
                    return
                content_length = resp.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_BOT_FILE_SIZE:
                    await message.answer(TEXTS["link_too_big"].format(max="20 MB"))
                    return
                data = await resp.read()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"دانلود لینک ناموفق: {e}")
        await message.answer(TEXTS["invalid_link"])
        return

    if len(data) > MAX_BOT_FILE_SIZE:
        await message.answer(TEXTS["link_too_big"].format(max="20 MB"))
        return

    filename = url.split("/")[-1].split("?")[0] or "file.bin"
    doc = BufferedInputFile(data, filename=filename)
    sent = await message.answer_document(doc)
    await state.clear()

    if sent.document is None:
        await message.answer(TEXTS["invalid_link"])
        return
    await _save_and_report(
        message, db,
        telegram_file_id=sent.document.file_id, ftype="document",
        size=len(data), name=filename, caption=None,
    )
