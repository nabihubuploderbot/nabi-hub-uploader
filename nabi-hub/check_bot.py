#!/usr/bin/env python3
"""check_bot.py — عیب‌یاب خودکار Nabi Hub | Uploader

اجرا:  python check_bot.py
(در همان پوشه‌ای که فایل .env پروژه است یا متغیرهای محیطی ست شده‌اند)

این اسکریپت مستقل است و ربات را اجرا نمی‌کند؛ فقط وضعیت را چک و گزارش می‌دهد:
  1) اعتبار توکن (getMe)
  2) وضعیت Webhook و آپدیت‌های معلق (getWebhookInfo)
  3) MAIN_ADMIN_ID
  4) اتصال دیتابیس و شمارش جداول
  5) اتصال Redis (اختیاری)
"""
import asyncio
import os
import re
import sys


def load_env() -> None:
    """بارگذاری .env اگر python-dotenv موجود باشد."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def line(char: str = "-", n: int = 60) -> str:
    return char * n


async def check_db(db_url: str) -> bool:
    """تست اتصال دیتابیس + شمارش ردیف‌ها / Check DB connection & counts."""
    from sqlalchemy import func, select, text

    from app.core.db import normalize_async_url
    from app.models.album import Album
    from app.models.admin import Admin
    from app.models.file import File
    from app.models.user import User
    from app.models.base import Base
    from sqlalchemy.ext.asyncio import create_async_engine

    url = normalize_async_url(db_url)
    print(f"   URL (نرمال‌شده): {url.split('@')[-1]}")
    engine = create_async_engine(url, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("   ✅ اتصال دیتابیس برقرار است.")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with engine.connect() as conn:
            users = (await conn.execute(select(func.count(User.id)))).scalar_one()
            files = (await conn.execute(select(func.count(File.id)))).scalar_one()
            admins = (await conn.execute(select(func.count(Admin.id)))).scalar_one()
            albums = (await conn.execute(select(func.count(Album.id)))).scalar_one()
            print(f"   👥 کاربران: {users} | 📁 فایل‌ها: {files} | 🗂 آلبوم‌ها: {albums} | 👑 ادمین‌ها: {admins}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"   ❌ اتصال دیتابیس ناموفق: {type(e).__name__}: {e}")
        return False
    finally:
        await engine.dispose()


async def check_redis(redis_url: str | None) -> None:
    """تست ردیس (اختیاری) / Optional Redis check."""
    if not redis_url:
        print("   ℹ️ REDIS_URL تنظیم نیست — FSM روی حافظهٔ رم اجرا می‌شود (برای شروع مشکلی نیست).")
        return
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(redis_url, decode_responses=True)
        await client.ping()
        print("   ✅ Redis متصل است.")
        await client.aclose()
    except Exception as e:  # noqa: BLE001
        print(f"   ⚠️ Redis متصل نشد (بحرانی نیست): {type(e).__name__}: {e}")


async def main() -> int:
    load_env()
    # مقادیر موقت تا ایمپورت app.core.settings در حین چک کرش نکند
    os.environ.setdefault("BOT_TOKEN", "000000:CHECK-BOT")
    os.environ.setdefault("MAIN_ADMIN_ID", "0")
    print("🔍 عیب‌یاب Nabi Hub | Uploader")
    print(line())

    problems: list[str] = []

    # ── 1) توکن ──
    token = (os.getenv("BOT_TOKEN") or "").strip()
    bot = None
    if not token:
        print("❌ BOT_TOKEN تنظیم نشده. فایل .env را از روی .env.example بسازید.")
        problems.append("BOT_TOKEN خالی است")
    elif not re.match(r"^\d+:[\w-]{20,}$", token):
        print("❌ فرمت BOT_TOKEN درست نیست — از @BotFather کامل کپی کنید (بدون فاصله/گیومه).")
        problems.append("فرمت BOT_TOKEN نامعتبر")
    else:
        print("✅ فرمت BOT_TOKEN درست است.")
        try:
            from aiogram import Bot

            bot = Bot(token=token)
            me = await bot.get_me()
            print(f"✅ توکن معتبر است: @{me.username} (bot id={me.id})")
        except Exception as e:  # noqa: BLE001
            print(f"❌ توکن نامعتبر یا دسترسی به تلگرام ممکن نیست: {type(e).__name__}: {e}")
            problems.append("getMe ناموفق — توکن را از @BotFather چک کنید")
            bot = None

    # ── 2) وضعیت Webhook ──
    if bot is not None:
        print(line())
        try:
            wi = await bot.get_webhook_info()
            if wi.url:
                print(f"⚠️ روی این توکن وب‌هوک تنظیم شده: {wi.url}")
                print("   → اگر ربات را با Polling اجرا می‌کنید، این تداخل است:")
                print("     تلگرام آپدیت‌ها را به آن URL می‌فرستد، نه به ربات شما!")
                problems.append("وب‌هوک قدیمی روی توکن فعال است")
            else:
                print("✅ وب‌هوکی روی توکن تنظیم نیست (Polling آزاد است).")
            print(f"   آپدیت‌های معلق: {wi.pending_update_count}")
            if wi.last_error_message:
                print(f"   ⚠️ آخرین خطای تحویل وب‌هوک: {wi.last_error_message}")
                problems.append("وب‌هوک خطای تحویل دارد")
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ دریافت وضعیت وب‌هوک ناموفق: {e}")

    # ── 3) MAIN_ADMIN_ID ──
    print(line())
    admin = (os.getenv("MAIN_ADMIN_ID") or "").strip()
    if not admin or not admin.isdigit() or admin == "111111111":
        print("❌ MAIN_ADMIN_ID واقعی نیست. شناسهٔ عددی خود را از @userinfobot بگیرید.")
        problems.append("MAIN_ADMIN_ID تنظیم نشده یا نمونه است")
    else:
        print(f"✅ MAIN_ADMIN_ID = {admin}")

    # ── 4) دیتابیس ──
    print(line())
    db_url = (os.getenv("DATABASE_URL") or "").strip()
    if not db_url:
        print("❌ DATABASE_URL تنظیم نشده.")
        problems.append("DATABASE_URL خالی است")
    else:
        try:
            await check_db(db_url)
        except Exception as e:  # noqa: BLE001
            print(f"   ❌ خطای غیرمنتظرهٔ دیتابیس: {e}")
            problems.append("دیتابیس قابل استفاده نیست")

    # ── 5) Redis ──
    print(line())
    await check_redis((os.getenv("REDIS_URL") or "").strip() or None)

    # ── جمع‌بندی ──
    print(line("="))
    if bot is not None:
        await bot.session.close()

    if problems:
        print("🚨 مشکلات پیدا شده:")
        for p in problems:
            print(f"   - {p}")
        print("\n💡 راهنمای کامل: فایل TROUBLESHOOT.md را بخوانید.")
        return 1
    print("✅ همه‌چیز سالم به نظر می‌رسد. ربات را با «python main.py» اجرا کنید و لاگ را ببینید.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
