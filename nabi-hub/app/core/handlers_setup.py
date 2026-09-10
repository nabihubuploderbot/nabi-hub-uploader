"""ثبت دستورات ربات در منوی تلگرام / Register bot commands in Telegram menu."""
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat

from app.core.settings import cfg

USER_COMMANDS = [
    BotCommand(command="start", description="شروع ربات و دریافت فایل"),
    BotCommand(command="done", description="پایان آپلود آلبوم"),
    BotCommand(command="cancel", description="لغو عملیات جاری"),
]

ADMIN_COMMANDS = [
    BotCommand(command="panel", description="پنل مدیریت"),
    BotCommand(command="stats", description="آمار ربات"),
    BotCommand(command="broadcast", description="ارسال همگانی"),
    *USER_COMMANDS,
]


async def set_bot_commands(bot: Bot) -> None:
    """ست دستورات عمومی و دستورات اختصاصی ادمین اصلی."""
    await bot.set_my_commands(USER_COMMANDS)
    try:
        await bot.set_my_commands(
            ADMIN_COMMANDS,
            scope=BotCommandScopeChat(chat_id=cfg.MAIN_ADMIN_ID),
        )
    except Exception:  # noqa: BLE001
        pass  # اگر ادمین هنوز ربات را استارت نکرده باشد خطا می‌دهد - بی‌خطر است
