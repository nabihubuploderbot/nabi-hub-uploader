"""ساخت Dispatcher و اتصال همهٔ روترها / Dispatcher & routers wiring.

ترتیب اجرا:
  Middlewareهای سراسری (Throttle → AdminFlag → UserUpsert → ForceJoin)
  سپس روترها به ترتیب: ادمین‌ها (با IsAdminFilter) → کاربران.

نکتهٔ حیاتی: AdminFlag باید outer_middleware باشد! در aiogram 3 ترتیب این است:
  outer_middleware → فیلترهای روتر → middleware (inbound) → هندلر
اگر AdminFlag inbound باشد، فیلتر IsAdminFilter قبل از ست‌شدن data["is_admin"]
ارزیابی می‌شود و کل پنل ادمین بی‌صدا از کار می‌افتد (هیچ خطایی هم لاگ نمی‌شود).
"""
import traceback

from aiogram import Dispatcher
from aiogram.fsm.storage.base import BaseStorage
from loguru import logger

from app.core.redis import RedisManager


def _register_global_error_handler(dp: Dispatcher) -> None:
    """هر خطای پردازش آپدیت را کامل لاگ می‌کند تا «هیچی نشدن» بی‌دلیل نباشد."""

    @dp.errors()
    async def _on_error(event) -> None:  # noqa: ANN001
        exc = getattr(event, "exception", None)
        if isinstance(exc, BaseException):
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            logger.error(f"⚠️ خطای پردازش آپدیت: {type(exc).__name__}: {exc}\n{tb[:3000]}")
        else:
            logger.error(f"⚠️ خطای پردازش آپدیت: {event!r}")


def build_dispatcher() -> Dispatcher:
    """ساخت Dispatcher با FSM Storage مناسب (Redis یا Memory) و ثبت روترها."""
    storage: BaseStorage = RedisManager.for_fsm()
    dp = Dispatcher(storage=storage)

    # ── Middlewares سراسری (به ترتیب اولویت) ──
    from app.middlewares.throttling import ThrottlingMiddleware
    from app.middlewares.user_upsert import UserUpsertMiddleware
    from app.middlewares.admin import AdminFlagMiddleware
    from app.middlewares.force_join import ForceJoinMiddleware

    for observer in (dp.message, dp.callback_query):
        # outer: قبل از فیلترها اجرا می‌شود (شرط حیاتی برای IsAdminFilter)
        observer.outer_middleware(AdminFlagMiddleware())
        # inbound: بعد از فیلترها و قبل از هندلر
        observer.middleware(ThrottlingMiddleware())
        observer.middleware(UserUpsertMiddleware())
        observer.middleware(ForceJoinMiddleware())

    _register_global_error_handler(dp)

    # ── Routers ──
    from app.handlers.user.start import router as start_router
    from app.handlers.user.download import router as download_router
    from app.handlers.user.upload import router as user_upload_router
    from app.handlers.user.reactions import router as reactions_router
    from app.handlers.admin.panel import router as panel_router
    from app.handlers.admin.general_settings import router as general_router
    from app.handlers.admin.advanced import router as advanced_router
    from app.handlers.admin.locks import router as locks_router
    from app.handlers.admin.broadcast import router as broadcast_router
    from app.handlers.admin.upload import router as admin_upload_router
    from app.handlers.admin.texts import router as texts_router
    from app.handlers.admin.stats import router as stats_router
    from app.handlers.admin.files import router as files_router
    from app.handlers.admin.users import router as users_router

    from app.middlewares.admin import IsAdminFilter

    admin_routers = (
        panel_router,
        general_router,
        advanced_router,
        locks_router,
        broadcast_router,
        admin_upload_router,
        texts_router,
        stats_router,
        files_router,
        users_router,
    )

    # روترهای ادمین فقط برای ادمین‌ها match می‌شوند (Filter → بدون بلاک بقیه)
    for r in admin_routers:
        r.message.filter(IsAdminFilter())
        r.callback_query.filter(IsAdminFilter())

    for r in (
        *admin_routers,
        reactions_router,
        download_router,
        user_upload_router,
        start_router,
    ):
        dp.include_router(r)

    return dp
