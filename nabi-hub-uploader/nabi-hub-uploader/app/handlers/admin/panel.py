"""پنل اصلی ادمین / Main admin panel."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.admin_panel import (
    advanced_settings_keyboard,
    general_settings_keyboard,
    main_panel_keyboard,
)

router = Router(name="admin_panel")


@router.message(Command("panel"))
async def cmd_panel(message: Message, state: FSMContext) -> None:
    """باز کردن پنل ادمین با دستور / Open admin panel via command."""
    await state.clear()
    await message.answer("🛠 <b>پنل مدیریت Nabi Hub</b>", reply_markup=main_panel_keyboard())


@router.callback_query(F.data == "panel:main")
async def cb_main(cb: CallbackQuery, state: FSMContext) -> None:
    """بازگشت به منوی اصلی پنل / Back to main panel."""
    await state.clear()
    await cb.message.edit_text(
        "🛠 <b>پنل مدیریت Nabi Hub</b>", reply_markup=main_panel_keyboard()
    )
    await cb.answer()


@router.callback_query(F.data == "panel:general")
async def cb_general(cb: CallbackQuery) -> None:
    """منوی تنظیمات کلی / General settings menu."""
    await cb.message.edit_text("⚙️ <b>تنظیمات کلی</b>", reply_markup=general_settings_keyboard())
    await cb.answer()


@router.callback_query(F.data == "panel:advanced")
async def cb_advanced(cb: CallbackQuery) -> None:
    """منوی تنظیمات پیشرفته / Advanced settings menu."""
    await cb.message.edit_text(
        "🔧 <b>تنظیمات پیشرفته</b>", reply_markup=advanced_settings_keyboard()
    )
    await cb.answer()
