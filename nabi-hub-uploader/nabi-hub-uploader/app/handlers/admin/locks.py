from app.states import AdminStates

"""مدیریت قفل‌ها (جوین اجباری + واکنش) / Locks management handlers."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from loguru import logger

from app.core.db import Database
from app.keyboards.locks import channels_list_keyboard, locks_menu_keyboard
from app.locales.fa import TEXTS
from app.services.lock_service import LockService
from app.services.settings_service import SettingsService

router = Router(name="admin_locks")


@router.callback_query(F.data == "locks:menu")
async def cb_locks_menu(cb: CallbackQuery, db: Database) -> None:
    """منوی مدیریت قفل‌ها / Locks menu."""
    await cb.message.edit_text("🔒 <b>مدیریت قفل‌ها</b>", reply_markup=locks_menu_keyboard())
    await cb.answer()


@router.callback_query(F.data == "locks:toggle_join")
async def cb_toggle_join(cb: CallbackQuery, db: Database) -> None:
    """روشن/خاموش جوین اجباری / Toggle force-join."""
    async with db.session_factory() as session:
        svc = SettingsService(session)
        settings = await svc.get()
        settings.force_join_enabled = not settings.force_join_enabled
        await svc.save(settings)
        state_txt = "🟢 فعال" if settings.force_join_enabled else "🔴 غیرفعال"
    await cb.answer(f"قفل جوین اجباری: {state_txt}", show_alert=True)


@router.callback_query(F.data == "locks:add")
async def cb_locks_add(cb: CallbackQuery, state: FSMContext) -> None:
    """افزودن کانال قفل / Add lock channel."""
    await state.set_state(AdminStates.waiting_channel)
    await cb.message.answer(
        "📢 کانال را فوروارد کنید یا @یوزرنیم/آیدی بفرستید:\n"
        "⚠️ توجه: ربات باید در کانال‌های خصوصی ادمین باشد."
    )
    await cb.answer()


@router.message(AdminStates.waiting_channel, F.text | F.forward_origin)
async def msg_locks_add(message: Message, state: FSMContext, db: Database) -> None:
    """دریافت کانال از فوروارد یا متن / Receive channel via forward or text."""
    chat_id: int | None = None
    username: str | None = None
    title: str | None = None

    if message.forward_origin is not None and message.forward_origin.chat is not None:
        chat = message.forward_origin.chat
        chat_id = chat.id
        title = chat.title
        username = getattr(chat, "username", None)
    elif message.text:
        raw = (message.text or "").strip().lstrip("@")
        if raw.startswith("-100"):
            try:
                chat_id = int(raw)
            except ValueError:
                chat_id = None
        elif raw:
            username = raw

    if chat_id is None and username is None:
        await message.answer(TEXTS["send_channel"])
        return

    # برای کانال عمومی، chat_id را از تلگرام می‌گیریم
    if chat_id is None and username:
        try:
            bot = message.bot
            chat = await bot.get_chat(f"@{username}")
            chat_id = chat.id
            title = chat.title
        except Exception as e:  # noqa: BLE001
            logger.warning(f"get_chat ناموفق برای @{username}: {e}")
            await message.answer("❌ کانال یافت نشد. یوزرنیم را چک کنید یا کانال را فوروارد کنید.")
            return

    async with db.session_factory() as session:
        svc = LockService(session)
        existing = await svc.find_channel_by_chat_id(chat_id)
        if existing is None:
            await svc.add_channel(chat_id, title=title, username=username)
            await message.answer(TEXTS["channel_added"])
        else:
            existing.is_active = True
            await session.commit()
            await message.answer("⚠️ این کانال قبلاً اضافه شده است.")
    await state.clear()


@router.callback_query(F.data == "locks:list")
async def cb_locks_list(cb: CallbackQuery, db: Database) -> None:
    """لیست کانال‌های قفل / List lock channels."""
    async with db.session_factory() as session:
        svc = LockService(session)
        channels = await svc.get_all_channels()
    await cb.message.edit_text(
        "📋 <b>کانال‌های قفل (برای حذف کلیک کنید):</b>",
        reply_markup=channels_list_keyboard(channels),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("locks:del:"))
async def cb_locks_del(cb: CallbackQuery, db: Database) -> None:
    """حذف کانال قفل / Remove lock channel."""
    channel_id = int(cb.data.split(":")[2])
    async with db.session_factory() as session:
        svc = LockService(session)
        await svc.remove_channel(channel_id)
        channels = await svc.get_all_channels()
    await cb.answer(TEXTS["channel_removed"], show_alert=True)
    await cb.message.edit_text(
        "📋 <b>کانال‌های قفل (برای حذف کلیک کنید):</b>",
        reply_markup=channels_list_keyboard(channels),
    )


# ── قفل واکنش / Reaction lock ──
@router.callback_query(F.data == "locks:reaction")
async def cb_reaction(cb: CallbackQuery, state: FSMContext) -> None:
    """تنظیم قفل واکنش: پست را فوروارد کنید / Set reaction lock: forward the post."""
    await state.set_state(AdminStates.waiting_reaction_post)
    await cb.message.answer(
        "👍 پستی که کاربران باید به آن واکنش بدهند را <b>فوروارد</b> کنید\n"
        "(ربات باید در آن کانال ادمین باشد):"
    )
    await cb.answer()


@router.message(AdminStates.waiting_reaction_post, F.forward_origin)
async def msg_reaction_post(message: Message, state: FSMContext, db: Database) -> None:
    """دریافت پست هدف برای قفل واکنش / Receive target post for reaction lock."""
    origin = message.forward_origin
    if origin is None or getattr(origin, "chat", None) is None:
        await message.answer("❌ لطفاً پست را از کانال فوروارد کنید.")
        return

    chat = origin.chat
    chat_id = chat.id
    # message_id اصلی از فوروارد کانال قابل استخراج است
    origin_message_id = getattr(origin, "message_id", None)
    if origin_message_id is None:
        await message.answer(
            "❌ شناسهٔ پیام اصلی در دسترس نیست. لینک پست را بفرستید "
            "(مثلاً https://t.me/channel/123):"
        )
        await state.set_state(AdminStates.waiting_reaction_emoji)
        await state.update_data(chat_id=chat_id)
        return

    async with db.session_factory() as session:
        svc = LockService(session)
        await svc.set_reaction_lock(chat_id, origin_message_id)
        set_svc = SettingsService(session)
        settings = await set_svc.get()
        settings.reaction_lock_enabled = True
        await set_svc.save(settings)
    await state.clear()
    await message.answer(TEXTS["reaction_set"] + "\n✅ قفل واکنش فعال شد.")


@router.message(AdminStates.waiting_reaction_emoji, F.text)
async def msg_reaction_link(message: Message, state: FSMContext, db: Database) -> None:
    """دریافت لینک پست (t.me/channel/123) / Receive post link."""
    import re

    data = await state.get_data()
    chat_id = data.get("chat_id")
    raw = (message.text or "").strip()
    m = re.match(r"https?://t\.me/([\w]+)/(\d+)", raw)
    if not m or chat_id is None:
        await message.answer("❌ لینک نامعتبر. فرمت: https://t.me/channel/123")
        return

    username, message_id = m.group(1), int(m.group(2))
    try:
        chat = await message.bot.get_chat(f"@{username}")
        chat_id = chat.id
    except Exception:  # noqa: BLE001
        pass

    async with db.session_factory() as session:
        svc = LockService(session)
        await svc.set_reaction_lock(chat_id, message_id)
        set_svc = SettingsService(session)
        settings = await set_svc.get()
        settings.reaction_lock_enabled = True
        await set_svc.save(settings)
    await state.clear()
    await message.answer(TEXTS["reaction_set"])


@router.callback_query(F.data == "locks:reaction_off")
async def cb_reaction_off(cb: CallbackQuery, db: Database) -> None:
    """غیرفعال‌سازی قفل واکنش / Deactivate reaction lock."""
    async with db.session_factory() as session:
        svc = LockService(session)
        await svc.deactivate_reaction_lock()
        set_svc = SettingsService(session)
        settings = await set_svc.get()
        settings.reaction_lock_enabled = False
        await set_svc.save(settings)
    await cb.answer("⛔ قفل واکنش غیرفعال شد.", show_alert=True)
