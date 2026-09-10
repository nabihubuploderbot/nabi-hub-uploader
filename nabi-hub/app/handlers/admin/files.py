from app.states import AdminStates

"""مدیریت فایل‌ها / Files management handlers."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core.db import Database
from app.keyboards.files import cancel_keyboard, files_menu_keyboard
from app.locales.fa import TEXTS
from app.services.file_service import FileService

router = Router(name="admin_files")


@router.callback_query(F.data == "files:manage")
async def cb_files_menu(cb: CallbackQuery) -> None:
    """منوی مدیریت فایل / Files management menu."""
    await cb.message.edit_text("📁 <b>مدیریت فایل‌ها</b>", reply_markup=files_menu_keyboard())
    await cb.answer()


@router.callback_query(F.data == "files:delete")
async def cb_files_delete(cb: CallbackQuery, state: FSMContext) -> None:
    """حذف فایل با کد / Delete file by code."""
    await state.set_state(AdminStates.waiting_delete_code)
    await cb.message.answer("🆔 کد فایل موردنظر را بفرستید:", reply_markup=cancel_keyboard())
    await cb.answer()


@router.message(AdminStates.waiting_delete_code, F.text)
async def msg_files_delete(message: Message, state: FSMContext, db: Database) -> None:
    code = (message.text or "").strip()
    async with db.session_factory() as session:
        svc = FileService(session)
        deleted = await svc.delete_by_code(code)
    await state.clear()
    if deleted:
        await message.answer(TEXTS["file_deleted"].format(code=code))
    else:
        await message.answer(TEXTS["not_found"])


@router.callback_query(F.data == "files:password")
async def cb_files_password(cb: CallbackQuery, state: FSMContext) -> None:
    """تنظیم پسورد برای فایل / Set file password."""
    await state.set_state(AdminStates.waiting_file_password)
    await cb.message.answer("🆔 کد فایل را بفرستید:")
    await cb.answer()


@router.message(AdminStates.waiting_file_password, F.text)
async def msg_files_password_code(message: Message, state: FSMContext, db: Database) -> None:
    """گرفتن کد فایل و سپس پسورد / Get file code then password."""
    data = await state.get_data()
    if "file_code" not in data:
        code = (message.text or "").strip()
        async with db.session_factory() as session:
            svc = FileService(session)
            file = await svc.get_by_code(code)
        if file is None:
            await message.answer(TEXTS["not_found"])
            return
        await state.update_data(file_code=code)
        await message.answer("🔑 پسورد جدید را بفرستید (- برای حذف):")
        return

    # مرحلهٔ دوم: دریافت پسورد
    code = data["file_code"]
    pwd = (message.text or "").strip()
    async with db.session_factory() as session:
        svc = FileService(session)
        file = await svc.get_by_code(code)
        if file is None:
            await message.answer(TEXTS["not_found"])
        else:
            file.password = None if pwd == "-" else pwd
            file.needs_password = pwd != "-"
            await session.commit()
            await message.answer(TEXTS["password_saved"])
    await state.clear()
