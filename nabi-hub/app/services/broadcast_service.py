"""سرویس ارسال همگانی / Broadcast service."""
import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import UserService


async def run_broadcast(
    bot: Bot,
    session: AsyncSession,
    source: Message,
    status_msg: Message,
    as_forward: bool = False,
) -> None:
    """ارسال همگانی با نرخ کنترل‌شده و گزارش پیشرفت.

    as_forward=True → پیام به‌صورت فوروارد ارسال می‌شود.
    """
    ids = await UserService(session).all_ids(only_active=True)
    total = len(ids)
    sent = failed = 0

    for i, uid in enumerate(ids, 1):
        try:
            if as_forward:
                await bot.copy_message(
                    chat_id=uid,
                    from_chat_id=source.chat.id,
                    message_id=source.message_id,
                )
            else:
                await source.copy_to(chat_id=uid)
            sent += 1
        except TelegramRetryAfter as e:
            # احترام به محدودیت نرخ تلگرام
            await asyncio.sleep(e.retry_after)
            try:
                await source.copy_to(chat_id=uid)
                sent += 1
            except TelegramAPIError:
                failed += 1
        except TelegramAPIError:
            failed += 1
        except Exception as e:  # noqa: BLE001
            logger.warning(f"broadcast خطا برای {uid}: {e}")
            failed += 1

        # گزارش پیشرفت هر ۲۵ نفر
        if i % 25 == 0 or i == total:
            try:
                await status_msg.edit_text(
                    f"📊 پیشرفت: {i}/{total}\n✅ {sent} | ⛔ {failed}"
                )
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(1)

    try:
        await status_msg.edit_text(
            f"✅ ارسال همگانی تمام شد.\n\n📤 موفق: {sent}\n⛔ ناموفق: {failed}"
        )
    except Exception:  # noqa: BLE001
        pass
    logger.info(f"broadcast done: sent={sent} failed={failed} total={total}")
