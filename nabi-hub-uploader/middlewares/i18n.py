"""
middlewares/i18n.py — Internationalization middleware.

Loads language strings from JSON files and provides them to handlers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, Any, Awaitable, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger


# ── Load locales ────────────────────────────────────
LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
LOCALES: Dict[str, Dict[str, str]] = {}


def load_locales() -> None:
    """Load all locale JSON files."""
    for locale_file in LOCALES_DIR.glob("*.json"):
        lang = locale_file.stem
        with open(locale_file, "r", encoding="utf-8") as f:
            LOCALES[lang] = json.load(f)
    logger.info(f"Loaded locales: {list(LOCALES.keys())}")


class I18nMiddleware(BaseMiddleware):
    """
    Internationalization middleware.

    Injects a 't' (translate) function into handler data.

    Usage in handlers:
        async def my_handler(message: Message, t: Callable[[str], str]):
            await t("welcome_message")
    """

    DEFAULT_LANG = "fa"

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Determine user language
        lang = self.DEFAULT_LANG
        if isinstance(event, Message) and event.from_user:
            lang = event.from_user.language_code or self.DEFAULT_LANG
        elif isinstance(event, CallbackQuery) and event.from_user:
            lang = event.from_user.language_code or self.DEFAULT_LANG

        # Normalize language code
        if lang not in LOCALES:
            lang = self.DEFAULT_LANG

        def t(key: str, **kwargs) -> str:
            """Translate a key using the user's locale."""
            locale = LOCALES.get(lang, LOCALES.get(self.DEFAULT_LANG, {}))
            template = locale.get(key, LOCALES.get(self.DEFAULT_LANG, {}).get(key, key))
            try:
                return template.format(**kwargs)
            except (KeyError, IndexError):
                return template

        data["t"] = t
        data["lang"] = lang

        return await handler(event, data)
