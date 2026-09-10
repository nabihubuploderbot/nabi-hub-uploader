from app.states import TextStates

"""تنظیم متون ربات / Bot texts management."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core.db import Database
from app.keyboards.texts_users import texts_menu_keyboard
from app.locales.fa import TEXTS
from app.services.settings_service import SettingsService

router = Router(name="admin_texts")


@router.callback_query(F.data == "texts:menu")
async def cb_texts_menu(cb: CallbackQuery) -> None:
    """منوی تنظیم متون / Texts menu."""
    await cb.message.edit_text("📝 <b>تنظیم متون ربات</b>", reply_markup=texts_menu_keyboard())
    await cb.answer()


@router.callback_query(F.data == "texts:start")
async def cb_text_start(cb: CallbackQuery, state: FSMContext) -> None:
    """ویرایش متن استارت / Edit start text."""
    await state.set_state(TextStates.waiting_start_text)
    await cb.message.answer(TEXTS["enter_text"])
    await cb.answer()


@router.message(TextStates.waiting_start_text, F.text)
async def msg_text_start(message: Message, state: FSMContext, db: Database) -> None:
    async with db.session_factory() as session:
        svc = SettingsService(session)
        settings = await svc.get()
        settings.start_text = message.text
        await svc.save(settings)
    await state.clear()
    await message.answer(TEXTS["text_updated"])


@router.callback_query(F.data == "texts:lock")
async def cb_text_lock(cb: CallbackQuery, state: FSMContext) -> None:
    """ویرایش متن قفل / Edit lock text."""
    await state.set_state(TextStates.waiting_lock_text)
    await cb.message.answer(TEXTS["enter_text"])
    await cb.answer()


@router.message(TextStates.waiting_lock_text, F.text)
async def msg_text_lock(message: Message, state: FSMContext, db: Database) -> None:
    async with db.session_factory() as session:
        svc = SettingsService(session)
        settings = await svc.get()
        settings.lock_text = message.text
        await svc.save(settings)
    await state.clear()
    await message.answer(TEXTS["text_updated"])


@router.callback_query(F.data == "texts:caption")
async def cb_text_caption(cb: CallbackQuery, state: FSMContext) -> None:
    """ویرایش کپشن پیش‌فرض / Edit default caption."""
    await state.set_state(TextStates.waiting_caption)
    await cb.message.answer(TEXTS["enter_caption"])
    await cb.answer()


@router.message(TextStates.waiting_caption, F.text)
async def msg_text_caption(message: Message, state: FSMContext, db: Database) -> None:
    cap = (message.text or "").strip()
    async with db.session_factory() as session:
        svc = SettingsService(session)
        settings = await svc.get()
        settings.default_caption = None if cap == "-" else cap
        await svc.save(settings)
    await state.clear()
    await message.answer(TEXTS["caption_set"])
