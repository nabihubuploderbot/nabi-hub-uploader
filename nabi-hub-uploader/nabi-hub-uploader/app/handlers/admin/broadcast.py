from app.states import AdminStates

"""ارسال همگانی و فوروارد همگانی / Broadcast & forward-broadcast handlers."""
import asyncio

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from app.core.db import Database
from app.keyboards.admin_panel import confirm_keyboard
from app.locales.fa import TEXTS
from app.services.user_service import UserService

router = Router(name="admin_broadcast")

# نگه‌داری پیام‌های در انتظار تأیید / Pending broadcast source messages
_pending: dict[int, dict] = {}
# تسک‌های فعال برای لغو / Active tasks for cancellation
_active_tasks: dict[int, asyncio.Task] = {}


@router.callback_query(F.data == "broadcast:start")
async def cb_broadcast(cb: CallbackQuery, state: FSMContext) -> None:
    """شروع فرآیند ارسال همگانی / Start broadcast flow."""
    await state.set_state(AdminStates.waiting_broadcast)
    await state.update_data(as_forward=False)
    await cb.message.answer(TEXTS["broadcast_prompt"])
    await cb.answer()


@router.callback_query(F.data == "broadcast:forward")
async def cb_forward(cb: CallbackQuery, state: FSMContext) -> None:
    """شروع فرآیند فوروارد همگانی / Start forward-broadcast flow."""
    await state.set_state(AdminStates.waiting_broadcast)
    await state.update_data(as_forward=True)
    await cb.message.answer("↗️ پیام/پستی که باید <b>فوروارد</b> شود را بفرستید:")
    await cb.answer()


@router.message(AdminStates.waiting_broadcast)
async def msg_broadcast(message: Message, state: FSMContext) -> None:
    """دریافت پیام همگانی و تأیید / Receive broadcast message & confirm."""
    data = await state.get_data()
    _pending[message.from_user.id] = {
        "chat_id": message.chat.id,
        "message_id": message.message_id,
        "as_forward": data.get("as_forward", False),
    }
    await message.answer(
        "📣 این پیام برای همهٔ کاربران ارسال شود؟",
        reply_markup=confirm_keyboard("broadcast:yes", "broadcast:no"),
    )


@router.callback_query(F.data == "broadcast:yes")
async def cb_broadcast_yes(cb: CallbackQuery, state: FSMContext, db: Database) -> None:
    """تأیید و اجرای ارسال همگانی در پس‌زمینه / Confirm & run broadcast in background."""
    info = _pending.pop(cb.from_user.id, None)
    await state.clear()
    if info is None:
        await cb.answer("خطا: پیام یافت نشد. دوباره تلاش کنید.", show_alert=True)
        return

    status = await cb.message.answer("🚀 ارسال همگانی آغاز شد ...")
    task = asyncio.create_task(
        _broadcast_task(
            bot=cb.bot,
            db=db,
            info=info,
            status_chat_id=status.chat.id,
            status_message_id=status.message_id,
        )
    )
    _active_tasks[cb.from_user.id] = task
    await cb.answer()


async def _broadcast_task(
    bot: Bot, db: Database, info: dict,
    status_chat_id: int, status_message_id: int,
) -> None:
    """اجرای ارسال همگانی با نرخ کنترل‌شده / Run throttled broadcast."""
    ids: list[int] = []
    async with db.session_factory() as session:
        ids = await UserService(session).all_ids(only_active=True)

    total = len(ids)
    sent = failed = 0

    for i, uid in enumerate(ids, 1):
        try:
            if info["as_forward"]:
                await bot.forward_message(
                    chat_id=uid,
                    from_chat_id=info["chat_id"],
                    message_id=info["message_id"],
                )
            else:
                await bot.copy_message(
                    chat_id=uid,
                    from_chat_id=info["chat_id"],
                    message_id=info["message_id"],
                )
            sent += 1
        except TelegramRetryAfter as e:
            # احترام به محدودیت نرخ تلگرام / Respect Telegram flood limit
            await asyncio.sleep(e.retry_after)
            try:
                await bot.copy_message(
                    chat_id=uid,
                    from_chat_id=info["chat_id"],
                    message_id=info["message_id"],
                )
                sent += 1
            except TelegramAPIError:
                failed += 1
        except TelegramAPIError:
            failed += 1
        except Exception as e:  # noqa: BLE001
            logger.warning(f"broadcast خطا برای {uid}: {e}")
            failed += 1

        # گزارش پیشرفت هر ۲۵ نفر / Progress report every 25 users
        if i % 25 == 0 or i == total:
            try:
                await bot.edit_message_text(
                    chat_id=status_chat_id,
                    message_id=status_message_id,
                    text=f"📊 پیشرفت: {i}/{total}\n✅ {sent} | ⛔ {failed}",
                )
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(1)

    try:
        await bot.edit_message_text(
            chat_id=status_chat_id,
            message_id=status_message_id,
            text=f"✅ ارسال همگانی تمام شد.\n\n📤 موفق: {sent}\n⛔ ناموفق: {failed}",
        )
    except Exception:  # noqa: BLE001
        pass
    logger.info(f"broadcast done: sent={sent} failed={failed} total={total}")


@router.callback_query(F.data == "broadcast:no")
async def cb_broadcast_no(cb: CallbackQuery, state: FSMContext) -> None:
    """لغو ارسال همگانی / Cancel broadcast."""
    _pending.pop(cb.from_user.id, None)
    await state.clear()
    await cb.message.edit_text(TEXTS["cancelled"])
    await cb.answer()


@router.callback_query(F.data == "broadcast:cancel_all")
async def cb_cancel_all(cb: CallbackQuery) -> None:
    """لغو تسک فعال / Cancel active broadcast task."""
    task = _active_tasks.pop(cb.from_user.id, None)
    if task:
        task.cancel()
        await cb.answer("🚫 ارسال همگانی لغو شد.", show_alert=True)
    else:
        await cb.answer("تسک فعالی وجود ندارد.", show_alert=True)
