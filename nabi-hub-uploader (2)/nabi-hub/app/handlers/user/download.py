"""هندلرهای دریافت فایل (کد + پسورد) / Download handlers (code + password)."""
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.core.db import Database
from app.locales.fa import TEXTS
from app.services.file_service import FileService
from app.services.settings_service import SettingsService
from app.services.user_service import UserService
from app.states import UserStates

router = Router(name="user_download")


@router.message(F.text.regexp(r"^[a-z0-9]{6,32}$"))
async def receive_code(message: Message, state: FSMContext, db: Database, user) -> None:
    """اگر کاربر مستقیماً کد فایل را تایپ کند، فایل را می‌فرستیم."""
    code = (message.text or "").strip()
    fs = FileService(db.session_factory)
    file = await fs.get_by_code(code)
    if file is None:
        return  # پیام معمولی است - نادیده می‌گیریم

    async with db.session_factory() as session:
        settings = await SettingsService(session).get()
        default_caption = settings.default_caption

    # پسورد سراسری یا پسورد فایل
    needed = file.password or (await _global_password(db))
    if needed and not user.unlocked_password:
        await state.update_data(pending_code=code)
        await state.set_state(UserStates.waiting_password)
        await message.answer(TEXTS["password_prompt"])
        return

    from app.handlers.user.start import send_media

    await fs.inc_download(file.id)
    await send_media(message, file.telegram_file_id, file.file_type, file.caption or default_caption)


@router.message(StateFilter(UserStates.waiting_password), F.text)
async def receive_password(message: Message, state: FSMContext, db: Database, user) -> None:
    """دریافت پسورد برای فایل قفل‌شده / Receive password for locked file."""
    data = await state.get_data()
    code = data.get("pending_code")
    if not code:
        await state.clear()
        return

    fs = FileService(db.session_factory)
    file = await fs.get_by_code(code)
    needed = (file.password if file else None) or (await _global_password(db))

    if needed and (message.text or "").strip() == needed:
        svc = UserService(db.session_factory)
        await svc.unlock_password(user.telegram_id)
        await state.clear()
        await message.answer(TEXTS["unlocked"])
        if file:
            from app.handlers.user.start import send_media

            await send_media(message, file.telegram_file_id, file.file_type, file.caption)
    else:
        await message.answer(TEXTS["wrong_password"])


async def _global_password(db: Database) -> str | None:
    async with db.session_factory() as session:
        settings = await SettingsService(session).get()
        return settings.global_password
