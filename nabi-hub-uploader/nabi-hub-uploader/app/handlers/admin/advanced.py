from app.states import AdminStates

"""تنظیمات پیشرفته: مدیریت ادمین‌ها / Advanced: admins management."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core.db import Database
from app.keyboards.texts_users import admins_menu_keyboard
from app.locales.fa import TEXTS
from app.services.admin_service import AdminService

router = Router(name="admin_advanced")


@router.callback_query(F.data == "admins:menu")
async def cb_admins_menu(cb: CallbackQuery, db: Database) -> None:
    """منوی مدیریت ادمین‌ها / Admins management menu."""
    await cb.message.edit_text("👑 <b>مدیریت ادمین‌ها</b>", reply_markup=admins_menu_keyboard())
    await cb.answer()


@router.callback_query(F.data == "admins:add")
async def cb_admins_add(cb: CallbackQuery, state: FSMContext) -> None:
    """افزودن ادمین / Add admin."""
    await state.set_state(AdminStates.waiting_admin_id)
    await cb.message.answer(TEXTS["give_id"])
    await cb.answer()


@router.message(AdminStates.waiting_admin_id, F.text)
async def msg_admins_add(message: Message, state: FSMContext, db: Database) -> None:
    try:
        tg_id = int((message.text or "").strip())
    except ValueError:
        await message.answer(TEXTS["give_id"])
        return

    async with db.session_factory() as session:
        svc = AdminService(session)
        if await svc.get(tg_id) is not None:
            await message.answer("⚠️ این کاربر قبلاً ادمین شده است.")
        else:
            await svc.add(tg_id)
            await message.answer(TEXTS["admin_added"])
    await state.clear()


@router.callback_query(F.data == "admins:remove")
async def cb_admins_remove(cb: CallbackQuery, state: FSMContext) -> None:
    """حذف ادمین / Remove admin."""
    await state.set_state(AdminStates.waiting_user_id)
    await state.update_data(mode="remove_admin")
    await cb.message.answer(TEXTS["give_id"])
    await cb.answer()


@router.callback_query(F.data == "admins:list")
async def cb_admins_list(cb: CallbackQuery, db: Database) -> None:
    """لیست ادمین‌ها / List admins."""
    async with db.session_factory() as session:
        admins = await AdminService(session).list_admins()
    lines = [
        f"{'👑' if a.is_main else '🔹'} <code>{a.telegram_id}</code> {a.full_name or ''}"
        for a in admins
    ]
    await cb.message.edit_text(
        "👑 <b>لیست ادمین‌ها</b>\n\n" + "\n".join(lines or ["—"]),
        reply_markup=admins_menu_keyboard(),
    )
    await cb.answer()

