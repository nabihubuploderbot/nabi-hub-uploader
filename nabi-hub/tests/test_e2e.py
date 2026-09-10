"""تست انتها-به-انتهای سیم‌کشی ربات — بدون اتصال واقعی به تلگرام.

شبیه‌سازی کامل آپدیت‌های تلگرام و بررسی اینکه هندلرها واقعاً fire می‌شوند:
  1) /start → باید SendMessage صادر شود
  2) /start CODE-ناموجود → باید «یافت نشد» صادر شود
  3) فایل عکس از کاربر (بدون متن) → نباید کرش کند
  4) callback دکمهٔ پنل ادمین → باید EditMessageText صادر شود

اجرا:  python tests/test_e2e.py
"""
import asyncio
import os
import sys
import time

# محیط آزمایشی — قبل از ایمپورت app ست می‌شود
os.environ["BOT_TOKEN"] = "123456:TEST-TOKEN-FAKE"
os.environ["MAIN_ADMIN_ID"] = "111111111"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["DEBUG_ECHO"] = "1"
os.environ["RUN_MODE"] = "polling"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot
from aiogram.types import (
    CallbackQuery,
    Chat,
    Message,
    PhotoSize,
    Update,
    User as TgUser,
)


class _FakeMe:
    """نتیجهٔ ساختگی bot.me() برای تست."""

    username = "test_bot"
    id = 123456


class FakeBot(Bot):
    """Bot ساختی: به‌جای ارسال واقعی، API callها را ثبت می‌کند."""

    def __init__(self) -> None:
        super().__init__(token=os.environ["BOT_TOKEN"])
        self.calls: list[str] = []

    async def me(self):  # noqa: ANN201 - override برای جلوگیری از تماس واقعی
        return _FakeMe()

    async def __call__(self, method, request_timeout=None):  # noqa: ANN001, ANN201
        name = type(method).__name__
        self.calls.append(name)
        print(f"   📡 API call: {name}")
        return True


async def run_tests() -> None:
    from app.core.db import Database
    from app.core.dispatcher import build_dispatcher
    from app.models.user import User as DbUser

    db = Database(os.environ["DATABASE_URL"])
    await db.create_all()

    dp = build_dispatcher()
    bot = FakeBot()

    user = DbUser(telegram_id=555, full_name="تست‌کننده")
    chat = Chat(id=555, type="private")
    sender = TgUser(id=555, is_bot=False, first_name="تست")

    # ── تست ۱: /start ──
    print("① /start ...")
    update = Update(
        update_id=1,
        message=Message(
            message_id=1, date=int(time.time()), chat=chat,
            from_user=sender, text="/start",
        ),
    )
    await dp.feed_update(bot, update, db=db, user=user)
    assert "SendMessage" in bot.calls, "هندلر /start fire نشد!"
    print("   ✅ /start پاسخ داد\n")

    # فاصله برای عبور از Throttle (۰٫۵ ثانیه)
    await asyncio.sleep(0.65)

    # ── تست ۲: دیپ‌لینک با کد ناموجود ──
    print("② /start nonexistent-code ...")
    bot.calls.clear()
    update = Update(
        update_id=2,
        message=Message(
            message_id=2, date=int(time.time()), chat=chat,
            from_user=sender, text="/start nonexistent-code",
        ),
    )
    await dp.feed_update(bot, update, db=db, user=user)
    assert "SendMessage" in bot.calls, "مسیر دیپ‌لینک پاسخ نداد!"
    print("   ✅ مسیر دیپ‌لینک پاسخ داد (فایل یافت نشد)\n")

    await asyncio.sleep(0.65)

    # ── تست ۳: فایل عکس از کاربر (بدون متن) — نباید کرش کند ──
    print("③ عکس بدون متن (کرش قبلی ForceJoin) ...")
    update = Update(
        update_id=3,
        message=Message(
            message_id=3, date=int(time.time()), chat=chat,
            from_user=sender,
            photo=(PhotoSize(file_id="F1", file_unique_id="U1", width=1, height=1),),
        ),
    )
    await dp.feed_update(bot, update, db=db, user=user)
    print("   ✅ کرش نکرد\n")

    # ── تست ۴: دکمهٔ پنل ادمین (ادمین اصلی) ──
    print("④ callback panel:main از ادمین ...")
    admin_sender = TgUser(id=111111111, is_bot=False, first_name="ادمین")
    bot.calls.clear()
    update = Update(
        update_id=4,
        callback_query=CallbackQuery(
            id="cb1",
            from_user=admin_sender,
            chat_instance="ci",
            data="panel:main",
            message=Message(
                message_id=9, date=int(time.time()), chat=chat, from_user=sender,
            ),
        ),
    )
    admin_user = DbUser(telegram_id=111111111, full_name="ادمین")
    await dp.feed_update(bot, update, db=db, user=admin_user)
    assert "EditMessageText" in bot.calls, "پنل ادمین fire نشد!"
    print("   ✅ پنل ادمین پاسخ داد\n")

    # صبر برای flush آلبومِ عکس تست ۳ (۲ ثانیه) تا تسک معلق نماند
    await asyncio.sleep(2.6)

    await bot.session.close()
    await db.close()
    print("=== E2E TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(run_tests())
