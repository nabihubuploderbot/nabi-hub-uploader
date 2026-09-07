"""
middlewares/auth.py — Admin authentication middleware.

Checks if the user is authorized to access admin features.
"""

from __future__ import annotations

from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings
from services.admin_service import AdminService


class AdminAuthMiddleware(BaseMiddleware):
    """
    Middleware to check if the user is an authorized admin.

    This middleware is applied only to admin handlers.
    It sets 'is_admin' and 'is_main_admin' in the handler data.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Extract user_id from the event
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        if user_id is None:
            return

        # Quick check: is user the main admin from config?
        is_main = user_id == settings.MAIN_ADMIN_ID
        data["is_main_admin"] = is_main

        # Check database for admin status
        session: AsyncSession = data.get("session")
        if session:
            is_admin = await AdminService.is_admin(session, user_id)
        else:
            # Fallback to config check
            is_admin = is_main

        data["is_admin"] = is_admin or is_main

        if not data["is_admin"]:
            logger.warning(f"Unauthorized admin access attempt: user_id={user_id}")
            if isinstance(event, Message):
                await event.answer("⛔ شما دسترسی ادمین ندارید.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return

        return await handler(event, data)
