"""ساخت نمونهٔ Bot با تنظیمات پیش‌فرض / Bot factory with default properties."""
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.settings import cfg


def build_bot() -> Bot:
    """ساخت Bot با پارس‌پیش‌فرض HTML و لینک‌های غیرفرستنده."""
    return Bot(
        token=cfg.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )
