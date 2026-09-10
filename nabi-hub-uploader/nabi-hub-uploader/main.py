"""Nabi Hub | Uploader - ربات آپلودر حرفه‌ای تلگرام
نقطهٔ ورود اصلی برنامه / Main entry point.
"""
import asyncio
import sys

from loguru import logger

from app.core.log import setup_logging
from app.core.settings import cfg


async def main() -> None:
    """اجرای کامل ربات: دیتابیس → ردیس → دیسپچر → Polling یا Webhook."""
    setup_logging()
    from app.core.db import Database
    from app.core.redis import RedisManager

    logger.info(f"🚀 در حال راه‌اندازی {cfg.BOT_NAME} ...")

    # اطمینان از وجود جداول پایگاه داده (برای تولید ساده؛ پروژهٔ رسمی از Alembic استفاده کنید)
    db = Database(cfg.DATABASE_URL)
    await db.create_all()

    # مدیریت ردیس: اگر URL داده نشود، None برمی‌گردد و FSM روی حافظه می‌ماند
    redis_manager = await RedisManager.connect(cfg.REDIS_URL)

    from app.core.bot_instance import build_bot
    bot = build_bot()

    from app.core.dispatcher import build_dispatcher
    dp = build_dispatcher()

    # ثبت خودکار دستورات در منوی تلگرام
    try:
        from app.core.handlers_setup import set_bot_commands
        await set_bot_commands(bot)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"ثبت دستورات ناموفق بود: {e}")

    # آغاز کاربران ادمین اصلی را خودکار می‌سازد
    try:
        from app.services.bootstrap import bootstrap_main_admin
        await bootstrap_main_admin(db.session_factory)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"bootstrap ادمین اصلی ناموفق: {e}")

    try:
        if cfg.is_webhook:
            await _run_webhook(bot, dp)
        else:
            logger.info("▶ شروع Polling ...")
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(
                bot,
                db=db,
                redis_manager=redis_manager,
                handle_signals=False,
            )
    finally:
        await bot.session.close()
        await db.close()
        await redis_manager.close()
        logger.info("⏹ ربات خاموش شد.")


async def _run_webhook(bot, dp) -> None:
    """اجرای ربات در حالت Webhook با وب‌سرور aiohttp (مناسب Railway)."""
    from aiogram.webhook.aiohttp_server import (
        SimpleRequestHandler,
        setup_application,
    )
    from aiohttp import web

    from app.core.dispatcher import build_dispatcher

    dp = build_dispatcher()
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(
        url=f"{cfg.WEBHOOK_URL.rstrip('/')}{cfg.WEBHOOK_PATH}",
        secret_token=cfg.SECRET_TOKEN or None,
        drop_pending_updates=True,
        allowed_updates=dp.resolve_used_update_types(),
    )

    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=cfg.SECRET_TOKEN or None,
    ).register(app, path=cfg.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=cfg.WEBAPP_HOST, port=cfg.WEBAPP_PORT)
    await site.start()
    logger.info(f"🌐 Webhook فعال روی پورت {cfg.WEBAPP_PORT} ...")
    await asyncio.Event().wait()  # اجرای همیشگی


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("خروج ...")
        sys.exit(0)
