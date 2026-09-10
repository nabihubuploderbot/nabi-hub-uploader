"""Nabi Hub | Uploader - ربات آپلودر حرفه‌ای تلگرام
نقطهٔ ورود اصلی برنامه / Main entry point.
"""
import asyncio
import sys

from loguru import logger

from app.core.log import setup_logging


async def main() -> None:
    """اجرای کامل ربات: تنظیمات → دیتابیس → ردیس → توکن → Polling یا Webhook."""
    setup_logging()

    # ── بارگذاری تنظیمات با پیام خطای فارسی و شفاف ──
    try:
        from app.core.settings import cfg
    except Exception as e:  # noqa: BLE001
        print(
            "\n❌ خطا در بارگذاری تنظیمات!\n"
            f"   {e}\n\n"
            "✅ راه‌حل: در پوشهٔ پروژه فایل .env را بر اساس .env.example بسازید و "
            "حداقل BOT_TOKEN و MAIN_ADMIN_ID را پر کنید. روی Railway هم این دو را در تب Variables ست کنید.\n"
        )
        sys.exit(1)

    logger.info(f"🚀 در حال راه‌اندازی {cfg.BOT_NAME} ...")
    logger.info(f"🧭 حالت اجرا: {cfg.run_mode.upper()}")

    from app.core.db import Database
    from app.core.redis import RedisManager

    db = Database(cfg.DATABASE_URL)
    await db.create_all()
    logger.info("🗄 دیتابیس آماده است.")

    redis_manager = await RedisManager.connect(cfg.REDIS_URL)

    from app.core.bot_instance import build_bot
    bot = build_bot()

    # ── پیش‌پرواز: اعتبارسنجی توکن قبل از شروع حلقه (خیلی مهم برای دیباگ) ──
    try:
        me = await bot.get_me()
        logger.info(f"🤖 توکن معتبر است: @{me.username}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"❌ توکن ربات نامعتبر است یا دسترسی به تلگرام ممکن نیست: {e}")
        logger.error("   راه‌حل: BOT_TOKEN را از @BotFather چک کنید و مطمئن شوید کامل کپی شده است.")
        await bot.session.close()
        await db.close()
        await redis_manager.close()
        sys.exit(1)

    from app.core.dispatcher import build_dispatcher
    dp = build_dispatcher()

    # ثبت خودکار دستورات در منوی تلگرام
    try:
        from app.core.handlers_setup import set_bot_commands
        await set_bot_commands(bot)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"ثبت دستورات ناموفق بود: {e}")

    # ساخت خودکار ادمین اصلی در دیتابیس
    try:
        from app.services.bootstrap import bootstrap_main_admin
        await bootstrap_main_admin(db.session_factory)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"bootstrap ادمین اصلی ناموفق: {e}")

    try:
        if cfg.run_mode == "webhook":
            await _run_webhook(bot, dp)
        else:
            await _run_polling(bot, dp, db, redis_manager)
    finally:
        await bot.session.close()
        await db.close()
        await redis_manager.close()
        logger.info("⏹ ربات خاموش شد.")


async def _run_polling(bot, dp, db, redis_manager) -> None:
    """اجرای Long Polling + لاگ وضعیت وب‌هوک برای تشخیص تداخل."""
    # وضعیت فعلی وب‌هوک روی این توکن (اگر جایی وب‌هوک ست باشد، آپدیت‌ها به آنجا می‌روند!)
    try:
        info = await bot.get_webhook_info()
        logger.info(
            f"🌐 وضعیت Webhook روی توکن: url={info.url or '—'} | "
            f"آپدیت‌های معلق={info.pending_update_count}"
        )
        if info.url:
            logger.warning(
                "⚠️ روی این توکن وب‌هوک تنظیم شده است؛ تلگرام آپدیت‌ها را به آن URL می‌فرستد نه به Polling."
            )
            logger.warning("   در ادامه وب‌هوک حذف می‌شود تا Polling درست کار کند.")
        if info.last_error_message:
            logger.warning(f"⚠️ آخرین خطای وب‌هوک ثبت‌شده: {info.last_error_message}")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"دریافت وضعیت وب‌هوک ناموفق: {e}")

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("▶ شروع Polling ... (برای تست سریع، DEBUG_ECHO=1 را هم ست کنید)")
    await dp.start_polling(
        bot,
        db=db,
        redis_manager=redis_manager,
        handle_signals=False,
    )


async def _run_webhook(bot, dp) -> None:
    """اجرای ربات در حالت Webhook با وب‌سرور aiohttp (مناسب Railway)."""
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
    from aiohttp import web

    from app.core.settings import cfg

    await bot.delete_webhook(drop_pending_updates=True)
    full_url = f"{cfg.WEBHOOK_URL.rstrip('/')}{cfg.WEBHOOK_PATH}"
    await bot.set_webhook(
        url=full_url,
        secret_token=cfg.SECRET_TOKEN or None,
        drop_pending_updates=True,
        allowed_updates=dp.resolve_used_update_types(),
    )
    logger.info(f"🌐 Webhook ثبت شد روی {full_url}")

    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=cfg.SECRET_TOKEN or None,
    ).register(app, path=cfg.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=cfg.WEBAPP_HOST, port=cfg.webapp_port)
    await site.start()
    logger.info(f"🌐 وب‌سرور فعال روی پورت {cfg.webapp_port} ...")
    await asyncio.Event().wait()  # اجرای همیشگی


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("خروج ...")
        sys.exit(0)
