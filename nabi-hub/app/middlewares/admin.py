"""چک ادمین / Admin check: flag middleware + router filter.

AdminFlagMiddleware → سراسری؛ فقط data["is_admin"] را ست می‌کند.
IsAdminFilter       → روی روترهای ادمین به‌عنوان Filter استفاده می‌شود؛
                      اگر False برگردد، هندلر match نمی‌شود و روتر بعدی
                      (هندلرهای کاربر عادی) به‌طور طبیعی ادامه می‌یابد.
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.filters import Filter

from app.core.db import Database
from app.services.admin_service import AdminService


class AdminFlagMiddleware(BaseMiddleware):
    """تعیین وضعیت ادمین بودن کاربر و گذاشتنش در data."""

    async def __call__(
        self,
        handler: Callable[[Any], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        db: Database | None = data.get("db")
        tg_user = data.get("event_from_user")
        data["is_admin"] = False
        if db is None or tg_user is None:
            return await handler(event, data)

        async with db.session_factory() as session:
            service = AdminService(session)
            data["is_admin"] = await service.is_admin(tg_user.id)
        return await handler(event, data)


class IsAdminFilter(Filter):
    """فیلتر گذرونده برای روترهای مدیریتی / Pass-through filter for admin routers."""

    async def __call__(self, event: Any, is_admin: bool = False) -> bool:
        return bool(is_admin)
