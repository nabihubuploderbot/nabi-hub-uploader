from app.states import UploadStates

"""آپلود کاربر عادی / Regular user upload (single + album)."""
import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from app.core.db import Database
from app.locales.fa import TEXTS
from app.services.file_service import FileService
from app.utils.helpers import extract_file, file_type_of, human_size

router = Router(name="user_upload")

_user_album_buffer: dict[int, dict] = {}
ALBUM_WAIT_SECONDS = 2.0


async def _flush_user_album(bot, db: Database, user_id: int) -> None:
    """ثبت نهایی فایل‌های بافرشدهٔ کاربر / Finalize user's buffered files."""
    data = _user_album_buffer.pop(user_id, None)
    if not data or not data["files"]:
        return
    files = data["files"]
    chat_id = data["chat_id"]
    try:
        async with db.session_factory() as session:
            svc = FileService(session)
            if len(files) == 1:
                f = files[0]
                file = await svc.create_file(
                    telegram_file_id=f["file_id"],
                    file_type=f["ftype"],
                    file_size=f["size"],
                    file_name=f["name"],
                    caption=f["caption"],
                    owner_id=user_id,
                )
                me = await bot.me()
                link = f"https://t.me/{me.username}?start={file.file_code}"
                await bot.send_message(
                    chat_id,
                    f"✅ فایل ثبت شد!\n💾 حجم: {human_size(f['size'])}\n🔗 لینک: <code>{link}</code>",
                )
            else:
                album = await svc.create_album(
                    title=f"آلبوم {len(files)} فایلی",
                    caption=next((f["caption"] for f in files if f["caption"]), None),
                    owner_id=user_id,
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
                        owner_id=user_id,
                    ))
                await session.commit()
                me = await bot.me()
                link = f"https://t.me/{me.username}?start={album.album_code}"
                await bot.send_message(
                    chat_id,
                    f"✅ آلبوم با <b>{len(files)}</b> فایل ثبت شد!\n🔗 لینک: <code>{link}</code>",
                )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"ثبت فایل کاربر ناموفق: {e}")


@router.message(F.photo | F.video | F.audio | F.voice | F.video_note | F.animation | F.document)
async def user_any_file(
    message: Message,
    state: FSMContext,
    db: Database,
    user,
) -> None:
    """هر فایلی که کاربر عادی می‌فرستد → خودکار ثبت و لینک برمی‌گردد.

    کاربر می‌تواند چند فایل پشت هم بفرستد (آلبوم تلگرام یا جدا جدا)؛
    بعد از ۲ ثانیه سکوت، همه به‌صورت یک بسته ثبت می‌شوند.
    """
    if user.is_banned:
        await message.answer(TEXTS["banned"])
        return

    file_id, size, name = extract_file(message)
    if file_id is None:
        return

    group_id = message.media_group_id or f"solo-{message.from_user.id}-{message.message_id}"
    caption = message.html_text if message.caption else None

    buffer = _user_album_buffer.setdefault(
        message.from_user.id,
        {"files": [], "task": None, "chat_id": message.chat.id},
    )
    buffer["files"].append({
        "file_id": file_id,
        "ftype": file_type_of(message),
        "size": size,
        "name": name,
        "caption": caption,
    })

    async def _deferred() -> None:
        await asyncio.sleep(ALBUM_WAIT_SECONDS)
        await _flush_user_album(message.bot, db, message.from_user.id)

    if buffer["task"]:
        buffer["task"].cancel()
    buffer["task"] = asyncio.create_task(_deferred())
