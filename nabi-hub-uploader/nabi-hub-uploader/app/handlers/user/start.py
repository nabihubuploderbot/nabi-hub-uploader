"""دستور استارت + دریافت فایل با دیپ‌لینک / Start command & deep-link file delivery."""
import asyncio

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from loguru import logger

from app.core.db import Database
from app.locales.fa import TEXTS
from app.services.file_service import FileService
from app.services.settings_service import SettingsService

router = Router(name="user_start")


@router.message(Command("start"))
async def cmd_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    db: Database,
    user,
) -> None:
    """نقطهٔ شروع: اگر آرگومان داشته باشد، فایل/آلبوم را می‌فرستد."""
    await state.clear()

    from app.services.settings_service import SettingsService as SS

    settings = await SS(db.session_factory).get()

    code = (command.args or "").strip() if command else ""
    if code:
        await deliver_by_code(message, db, code, settings, user)
        return

    text = settings.start_text or TEXTS["start"]
    await message.answer(text.format(name=user.full_name or "کاربر"))


async def deliver_by_code(message: Message, db: Database, code: str, settings, user) -> None:
    """ارسال فایل یا آلبوم بر اساس کد / Deliver file or album by its code."""
    if user and user.is_banned:
        await message.answer(TEXTS["banned"])
        return

    fs = FileService(db.session_factory)

    # ابتدا آلبوم، سپس فایل تکی
    album = await fs.get_album_by_code(code)
    if album is not None:
        files = await fs.album_files(album.id)
        if not files:
            await message.answer(TEXTS["not_found"])
            return
        await _optional_delay(message, settings.timer_seconds)
        for f in files:
            await send_media(message, f.telegram_file_id, f.file_type, f.caption or album.caption)
        await message.answer(TEXTS["album_done"].format(count=len(files), link=f"…?start={code}"))
        return

    file = await fs.get_by_code(code)
    if file is None:
        await message.answer(TEXTS["not_found"])
        return

    await _optional_delay(message, settings.timer_seconds)

    await send_media(
        message,
        file.telegram_file_id,
        file.file_type,
        file.caption or settings.default_caption,
    )
    await fs.inc_download(file.id)
    await message.answer(
        TEXTS["file_info"].format(
            code=file.file_code,
            ftype=file.file_type,
            size=f"{file.file_size / 1024 / 1024:.2f} MB",
            downloads=file.download_count,
            link=f"https://t.me/your_bot?start={file.file_code}",
        )
    )


async def _optional_delay(message: Message, seconds: int) -> None:
    """اگر تایمر تنظیم شده باشد، تأخیر قبل از ارسال / Optional timer before sending."""
    if seconds and seconds > 0:
        note = await message.answer(TEXTS["sending_in"].format(sec=seconds))
        await asyncio.sleep(min(seconds, 60))
        try:
            await note.delete()
        except Exception:  # noqa: BLE001
            pass


async def send_media(message: Message, file_id: str, ftype: str, caption: str | None) -> None:
    """ارسال مدیا بر اساس نوع / Send media based on its type."""
    kwargs = {"caption": caption} if caption else {}
    try:
        if ftype == "photo":
            await message.answer_photo(file_id, **kwargs)
        elif ftype == "video":
            await message.answer_video(file_id, **kwargs)
        elif ftype == "audio":
            await message.answer_audio(file_id, **kwargs)
        elif ftype == "voice":
            await message.answer_voice(file_id, **kwargs)
        elif ftype == "video_note":
            await message.answer_video_note(file_id)
        elif ftype == "animation":
            await message.answer_animation(file_id, **kwargs)
        else:
            await message.answer_document(file_id, **kwargs)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"ارسال مدیا ناموفق: {e}")
        await message.answer(TEXTS["not_found"])


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """لغو هر عملیات در جریان / Cancel any ongoing operation."""
    await state.clear()
    await message.answer(TEXTS["cancelled"])
