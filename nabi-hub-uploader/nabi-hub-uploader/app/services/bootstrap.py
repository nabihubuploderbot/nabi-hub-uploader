"""آماده‌سازی اولیه: ساخت ادمین اصلی / Bootstrap main admin."""
from sqlalchemy.ext.asyncio import async_sessionmaker

from loguru import logger

from app.core.settings import cfg
from app.services.admin_service import AdminService


async def bootstrap_main_admin(session_factory: async_sessionmaker) -> None:
    """اطمینان از وجود ادمین اصلی در جدول ادمین‌ها."""
    async with session_factory() as session:
        svc = AdminService(session)
        if await svc.get(cfg.MAIN_ADMIN_ID) is None:
            await svc.add(cfg.MAIN_ADMIN_ID, is_main=True)
            logger.info(f"👑 ادمین اصلی ساخته شد: {cfg.MAIN_ADMIN_ID}")
