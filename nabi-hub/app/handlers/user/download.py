"""هندلرهای دریافت فایل (کد + پسورد) / Download handlers (code + password).

نکته: سرویس‌ها AsyncSession می‌گیرند؛ همیشه داخل session context کار می‌کنیم.
"""
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

    async with db.session_factory() as session:
        fs = FileService(session)
        file = await fs.get_by_code(code)
        if file is None:
            return  # پیام معمولی است - نادیده می‌گیریم

        settings = await SettingsService(session).get()
        default_caption = settings.default_caption
        global_password = settings.global_password

    # پسورد سراسری یا پسورد فایل
    needed = file.password or global_password
    if needed and not user.unlocked_password:
        await state.update_data(pending_code=code)
        await state.set_state(UserStates.waiting_password)
        await message.answer(TEXTS["password_prompt"])
        return

    from app.handlers.user.start import send_media

    async with db.session_factory() as session:
        await FileService(session).inc_download(file.id)
    await send_media(message, file.telegram_file_id, file.file_type, file.caption or default_caption)


@router.message(StateFilter(UserStates.waiting_password), F.text)
async def receive_password(message: Message, state: FSMContext, db: Database, user) -> None:
    """دریافت پسورد برای فایل قفل‌شده / Receive password for locked file."""
    data = await state.get_data()
    code = data.get("pending_code")
    if not code:
        await state.clear()
        return

    async with db.session_factory() as session:
        fs = FileService(session)
        file = await fs.get_by_code(code)
        settings = await SettingsService(session).get()
        needed = (file.password if file else None) or settings.global_password

        if needed and (message.text or "").strip() == needed:
            await UserService(session).unlock_password(user.telegram_id)
            await state.clear()
            await message.answer(TEXTS["unlocked"])
            if file:
                from app.handlers.user.start import send_media

                await send_media(message, file.telegram_file_id, file.file_type, file.caption)
        else:
            await message.answer(TEXTS["wrong_password"])
