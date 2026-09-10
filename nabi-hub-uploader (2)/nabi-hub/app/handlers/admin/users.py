from app.states import AdminStates

"""مدیریت کاربران / Users management handlers."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core.db import Database
from app.keyboards.texts_users import users_menu_keyboard
from app.locales.fa import TEXTS
from app.services.user_service import UserService

router = Router(name="admin_users")


@router.callback_query(F.data == "users:menu")
async def cb_users_menu(cb: CallbackQuery) -> None:
    """منوی مدیریت کاربر / Users management menu."""
    await cb.message.edit_text("👤 <b>مدیریت کاربران</b>", reply_markup=users_menu_keyboard())
    await cb.answer()


async def _ban_flow(cb: CallbackQuery, state: FSMContext, banned: bool) -> None:
    await state.set_state(AdminStates.waiting_user_id)
    await state.update_data(ban_mode=banned)
    await cb.message.answer(TEXTS["give_id"])
    await cb.answer()


@router.callback_query(F.data == "users:ban")
async def cb_users_ban(cb: CallbackQuery, state: FSMContext) -> None:
    """مسدودسازی کاربر / Ban user."""
    await _ban_flow(cb, state, True)


@router.callback_query(F.data == "users:unban")
async def cb_users_unban(cb: CallbackQuery, state: FSMContext) -> None:
    """رفع مسدودی / Unban user."""
    await _ban_flow(cb, state, False)


@router.message(AdminStates.waiting_user_id, F.text)
async def msg_user_id(message: Message, state: FSMContext, db: Database) -> None:
    """دریافت شناسهٔ کاربر برای مسدودسازی/رفع یا حذف ادمین / Receive user id."""
    data = await state.get_data()
    try:
        tg_id = int((message.text or "").strip())
    except ValueError:
        await message.answer(TEXTS["give_id"])
        return

    mode = data.get("mode")
    if mode == "remove_admin":
        async with db.session_factory() as session:
            from app.services.admin_service import AdminService

            result = await AdminService(session).remove(tg_id)
        await state.clear()
        if result == "main":
            await message.answer(TEXTS["admin_main_protected"])
        elif result == "ok":
            await message.answer(TEXTS["admin_removed"])
        else:
            await message.answer(TEXTS["not_found"])
        return

    banned = data.get("ban_mode", True)
    async with db.session_factory() as session:
        svc = UserService(session)
        ok = await svc.set_ban(tg_id, banned)
    await state.clear()
    if ok:
        await message.answer(TEXTS["user_banned"] if banned else TEXTS["user_unbanned"])
    else:
        await message.answer(TEXTS["not_found"])


@router.callback_query(F.data == "users:list")
async def cb_users_list(cb: CallbackQuery, db: Database) -> None:
    """آخرین کاربران / Latest users."""
    async with db.session_factory() as session:
        users = await UserService(session).list_users(limit=15)
    lines = [
        f"{'⛔' if u.is_banned else '✅'} <code>{u.telegram_id}</code> {u.full_name or ''}"
        for u in users
    ]
    await cb.message.edit_text(
        "👥 <b>آخرین کاربران:</b>\n\n" + "\n".join(lines or ["—"]),
        reply_markup=users_menu_keyboard(),
    )
    await cb.answer()
