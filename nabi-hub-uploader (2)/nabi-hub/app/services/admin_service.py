"""سرویس ادمین‌ها / Admin service."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import cfg
from app.models.admin import Admin


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, telegram_id: int) -> Admin | None:
        res = await self.session.execute(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )
        return res.scalar_one_or_none()

    async def is_admin(self, telegram_id: int) -> bool:
        """ادمین اصلی همیشه ادمین است + ادمین‌های جدول."""
        if telegram_id == cfg.MAIN_ADMIN_ID:
            return True
        return await self.get(telegram_id) is not None

    async def add(self, telegram_id: int, username: str | None = None,
                  full_name: str | None = None, is_main: bool = False) -> Admin:
        admin = Admin(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            is_main=is_main,
        )
        self.session.add(admin)
        await self.session.commit()
        return admin

    async def remove(self, telegram_id: int) -> str:
        """حذف ادمین؛ ادمین اصلی محافظت می‌شود."""
        if telegram_id == cfg.MAIN_ADMIN_ID:
            return "main"
        admin = await self.get(telegram_id)
        if admin is None:
            return "not_found"
        await self.session.delete(admin)
        await self.session.commit()
        return "ok"

    async def count(self) -> int:
        res = await self.session.execute(select(func.count(Admin.id)))
        return int(res.scalar_one())

    async def list_admins(self) -> list[Admin]:
        res = await self.session.execute(select(Admin).order_by(Admin.id))
        return list(res.scalars().all())
