"""
main.py — Entry point for Nabi Hub | Uploader Telegram Bot.

Initializes the bot, registers middleware, sets up database,
and starts either webhook or long-polling mode.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from loguru import logger

from config import settings

# ── Configure Logging ───────────────────────────────
logger.remove()
logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
)
logger.add(
    "logs/bot.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
)


# ── Initialize Bot ──────────────────────────────────
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
        link_preview_is_disabled=True,
    ),
)

# ── Initialize Dispatcher ───────────────────────────
dp = Dispatcher(storage=MemoryStorage())


async def setup_middlewares() -> None:
    """Register all middlewares on the dispatcher."""
    import redis.asyncio as aioredis

    from middlewares.db import DatabaseMiddleware
    from middlewares.throttle import ThrottleMiddleware
    from middlewares.force_join import ForceJoinMiddleware
    from middlewares.i18n import I18nMiddleware, load_locales
    from middlewares.auth import AdminAuthMiddleware

    # Load locales
    load_locales()

    # Redis client for throttle middleware
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )

    # Test Redis connection
    try:
        await redis_client.ping()
        logger.info("✅ Redis connected successfully")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        redis_client = None

    # Register middlewares in order (outermost first)
    # 1. Database session middleware (runs for ALL updates)
    dp.update.middleware(DatabaseMiddleware())

    # 2. Internationalization middleware
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())

    # 3. Rate limiting middleware (if Redis is available)
    if redis_client:
        throttle = ThrottleMiddleware(redis=redis_client, rate_limit=5, time_window=3)
        dp.message.middleware(throttle)
        dp.callback_query.middleware(throttle)

        # 4. Force join middleware (applied to messages and callbacks)
    dp.message.middleware(ForceJoinMiddleware())
    dp.callback_query.middleware(ForceJoinMiddleware())

    # 5. Admin authentication — attached ONLY to admin + upload routers.
    #    (Registering it on dp.message/dp.callback_query blocked EVERY
    #    non-admin update: regular users could never download files.)
    from handlers.admin_panel import router as admin_panel_router
    from handlers.admin_settings import router as admin_settings_router
    from handlers.admin_broadcast import router as admin_broadcast_router
    from handlers.admin_files import router as admin_files_router
    from handlers.admin_users import router as admin_users_router
    from handlers.admin_channel import router as admin_channel_router
    from handlers.admin_manage import router as admin_manage_router
    from handlers.upload import router as upload_router

    for _admin_router in (
        admin_panel_router,
        admin_settings_router,
        admin_broadcast_router,
        admin_files_router,
        admin_users_router,
        admin_channel_router,
        admin_manage_router,
        upload_router,
    ):
        _admin_router.message.middleware(AdminAuthMiddleware())
        _admin_router.callback_query.middleware(AdminAuthMiddleware())

    logger.info("✅ All middlewares registered")



async def setup_handlers() -> None:
    """Register all handler routers."""
    from handlers import get_handlers_router

    main_router = get_handlers_router()
    dp.include_router(main_router)

    logger.info("✅ All handlers registered")


async def setup_bot_commands() -> None:
    """Set bot commands menu."""
    user_commands = [
        BotCommand(command="start", description="شروع ربات"),
        BotCommand(command="help", description="راهنمای ربات"),
    ]

    admin_commands = user_commands + [
        BotCommand(command="admin", description="پنل مدیریت"),
        BotCommand(command="stats", description="آمار ربات"),
        BotCommand(command="channels", description="لیست کانال‌ها"),
        BotCommand(command="admins", description="لیست ادمین‌ها"),
        BotCommand(command="addadmin", description="افزودن ادمین"),
        BotCommand(command="removeadmin", description="حذف ادمین"),
        BotCommand(command="addchannel", description="افزودن کانال قفل"),
        BotCommand(command="removechannel", description="حذف کانال قفل"),
        BotCommand(command="addreaction", description="افزودن قفل واکنش"),
        BotCommand(command="setwelcome", description="تنظیم پیام خوش‌آمدگویی"),
        BotCommand(command="setcaption", description="تنظیم کپشن"),
        BotCommand(command="setdelay", description="تنظیم تایمر"),
        BotCommand(command="setpassword", description="تنظیم پسورد"),
    ]

    # Set commands for all users
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # Set admin commands for main admin
    await bot.set_my_commands(
        admin_commands,
        scope=BotCommandScopeChat(chat_id=settings.MAIN_ADMIN_ID),
    )

    logger.info("✅ Bot commands set")


async def init_database() -> None:
    """Initialize database tables and default data."""
    from models.base import init_db, async_session
    from services.admin_service import AdminService
    from services.setting_service import SettingService

    # Create tables
    await init_db()
    logger.info("✅ Database tables created/verified")

    # Initialize main admin
    async with async_session() as session:
        # Try to get bot info for admin name
        me = await bot.get_me()
        await AdminService.get_or_create_main_admin(
            session=session,
            user_id=settings.MAIN_ADMIN_ID,
        )

        # Initialize default settings
        await SettingService.init_defaults(session)

    logger.info(f"✅ Main admin registered: {settings.MAIN_ADMIN_ID}")


async def on_startup() -> None:
    """Actions to perform on bot startup."""
    logger.info("🚀 Starting Nabi Hub | Uploader Bot...")

    # Initialize database
    await init_database()

    # Setup middlewares
    await setup_middlewares()

    # Setup handlers
    await setup_handlers()

    # Set bot commands
    await setup_bot_commands()

    # Delete webhook if switching to polling
    if not settings.USE_WEBHOOK:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook deleted (using polling mode)")

    logger.info("✅ Bot started successfully!")


async def on_shutdown() -> None:
    """Actions to perform on bot shutdown."""
    logger.info("🛑 Shutting down bot...")

    from models.base import close_db
    await close_db()

    await bot.session.close()
    logger.info("✅ Bot shut down cleanly")


async def main() -> None:
    """Main entry point."""
    # Run startup
    await on_startup()

    try:
        if settings.USE_WEBHOOK:
            # ── Webhook Mode ────────────────────────
            from aiohttp import web
            from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

            # Create webhook request handler
            webhook_handler = SimpleRequestHandler(
                dispatcher=dp,
                bot=bot,
                secret_token=settings.SECRET_TOKEN,
            )

            # Create aiohttp application
            app = web.Application()
            webhook_handler.register(app, path=settings.WEBHOOK_PATH)
            setup_application(app, dp, bot=bot)

            # Set webhook
            await bot.set_webhook(
                url=settings.webhook_url_full,
                secret_token=settings.SECRET_TOKEN,
                drop_pending_updates=True,
            )
            logger.info(f"✅ Webhook set: {settings.webhook_url_full}")

            # Start web server
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(
                runner,
                host=settings.WEBAPP_HOST,
                port=settings.WEBAPP_PORT,
            )
            await site.start()

            logger.info(
                f"🌐 Webhook server running on "
                f"{settings.WEBAPP_HOST}:{settings.WEBAPP_PORT}"
            )

            # Keep running
            try:
                await asyncio.Event().wait()
            finally:
                await runner.cleanup()

        else:
            # ── Long Polling Mode ───────────────────
            logger.info("🔄 Starting long polling...")
            await dp.start_polling(
                bot,
                allowed_updates=[
                    "message",
                    "callback_query",
                    "chat_member",
                    "my_chat_member",
                    "chat_join_request",
                ],
            )

    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        sys.exit(1)
