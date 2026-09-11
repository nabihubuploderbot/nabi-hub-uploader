"""
middlewares/db.py — Database session middleware.

Provides a SQLAlchemy async session to all handlers.
"""

from __future__ import annotations

from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import async_session


class DatabaseMiddleware(BaseMiddleware):
    """
    Creates a new database session for each update and injects it
    into the handler data dict.

    Usage in handlers:
        async def my_handler(message: Message, session: AsyncSession):
            ...
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["session"] = session
            try:
                return await handler(event, data)
            except Exception:
                await session.rollback()
                raise
