from app.states import AdminStates

"""تنظیمات کلی ادمین / General settings handlers (power, toggles, channels)."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from loguru import logger

from app.core.db import Database
from app.locales.fa import TEXTS
from app.services.settings_service import SettingsService

router = Router(name="admin_general")


async def _get_settings(db: Database):
    async with db.session_factory() as session:
        svc = SettingsService(session)
        return await svc.get()


@router.callback_query(F.data == "settings:power")
async def cb_power(cb: CallbackQuery, db: Database) -> None:
    """روشن/خاموش کردن ربات / Toggle bot power."""
    async with db.session_factory() as session:
        svc = SettingsService(session)
        settings = await svc.get()
        settings.bot_enabled = not settings.bot_enabled
        await svc.save(settings)
        state_txt = "🟢 روشن" if settings.bot_enabled else "🔴 خاموش"
    await cb.answer(f"ربات: {state_txt}", show_alert=True)


@router.callback_query(F.data == "settings:toggle_channel")
async def cb_toggle_channel(cb: CallbackQuery, db: Database) -> None:
    """ارسال خودکار فایل‌ها به کانال / Auto-send files to channel toggle."""
    async with db.session_factory() as session:
        svc = SettingsService(session)
        settings = await svc.get()
        settings.send_to_channel = not settings.send_to_channel
        await svc.save(settings)
        state_txt = "🟢 فعال" if settings.send_to_channel else "🔴 غیرفعال"
    await cb.answer(f"ارسال به کانال: {state_txt}", show_alert=True)


@router.callback_query(F.data == "settings:group")
async def cb_group(cb: CallbackQuery, state: FSMContext) -> None:
    """دریافت شناسهٔ گروه / Get group id."""
    await state.set_state(AdminStates.waiting_group)
    await cb.message.answer("👥 شناسهٔ عددی گروه را بفرستید (-100...):")
    await cb.answer()


@router.message(AdminStates.waiting_group, F.text)
async def msg_group(message: Message, state: FSMContext, db: Database) -> None:
    async with db.session_factory() as session:
        svc = SettingsService(session)
        settings = await svc.get()
        settings.group_id = (message.text or "").strip()
        await svc.save(settings)
    await state.clear()
    await message.answer(TEXTS["group_saved"])


@router.callback_query(F.data == "settings:log_channel")
async def cb_log_channel(cb: CallbackQuery, state: FSMContext) -> None:
    """دریافت کانال ثبت / Get log channel."""
    await state.set_state(AdminStates.waiting_log_channel)
    await cb.message.answer("📡 شناسهٔ کانال ثبت را بفرستید (-100...):")
    await cb.answer()


@router.message(AdminStates.waiting_log_channel, F.text)
async def msg_log_channel(message: Message, state: FSMContext, db: Database) -> None:
    async with db.session_factory() as session:
        svc = SettingsService(session)
        settings = await svc.get()
        settings.channel_log_id = (message.text or "").strip()
        await svc.save(settings)
    await state.clear()
    await message.answer(TEXTS["log_channel_saved"])


@router.callback_query(F.data == "settings:buttons")
async def cb_buttons(cb: CallbackQuery, db: Database) -> None:
    """مدیریت دکمه‌ها: نمایش/مخفی‌کردن دکمهٔ لینک زیر فایل / Manage link button."""
    async with db.session_factory() as session:
        svc = SettingsService(session)
        current = await svc.get_kv("show_link_button")
        new_val = "off" if current == "on" else "on"
        await svc.set_kv("show_link_button", new_val)
    await cb.answer(f"دکمهٔ لینک: {'✅ روشن' if new_val == 'on' else '⛔ خاموش'}", show_alert=True)


@router.callback_query(F.data == "settings:sin")
async def cb_sin(cb: CallbackQuery, db: Database) -> None:
    """تنظیمات سین: حالت محافظت‌شده (جلوگیری از ذخیره) / Protected-content mode."""
    async with db.session_factory() as session:
        svc = SettingsService(session)
        current = await svc.get_kv("protect_content")
        new_val = "off" if current == "on" else "on"
        await svc.set_kv("protect_content", new_val)
    await cb.answer(f"محافظت محتوا: {'✅ روشن' if new_val == 'on' else '⛔ خاموش'}", show_alert=True)


# ── تایمر و پسورد (منوی پیشرفته) ──
@router.callback_query(F.data == "settings:timer")
async def cb_timer(cb: CallbackQuery, state: FSMContext) -> None:
    """تنظیم تایمر ارسال / Set send timer."""
    await state.set_state(AdminStates.waiting_timer)
    await cb.message.answer(TEXTS["give_number"] + "\n(ثانیه، 0 = بدون تأخیر)")
    await cb.answer()


@router.message(AdminStates.waiting_timer, F.text)
async def msg_timer(message: Message, state: FSMContext, db: Database) -> None:
    try:
        seconds = max(0, min(int((message.text or "0").strip()), 300))
    except ValueError:
        await message.answer(TEXTS["give_number"])
        return
    async with db.session_factory() as session:
        svc = SettingsService(session)
        settings = await svc.get()
        settings.timer_seconds = seconds
        await svc.save(settings)
    await state.clear()
    await message.answer(TEXTS["timer_set"].format(sec=seconds))


@router.callback_query(F.data == "settings:password")
async def cb_password(cb: CallbackQuery, state: FSMContext) -> None:
    """تنظیم پسورد سراسری / Set global password."""
    await state.set_state(AdminStates.waiting_password)
    await cb.message.answer("🔑 پسورد سراسری را بفرستید (- برای حذف):")
    await cb.answer()


@router.message(AdminStates.waiting_password, F.text)
async def msg_password(message: Message, state: FSMContext, db: Database) -> None:
    pwd = (message.text or "").strip()
    async with db.session_factory() as session:
        svc = SettingsService(session)
        settings = await svc.get()
        settings.global_password = None if pwd == "-" else pwd
        await svc.save(settings)
    await state.clear()
    await message.answer(TEXTS["password_saved"])
