"""سرویس کاربران / User service."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.helpers import utc_now


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        res = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return res.scalar_one_or_none()

    async def get_or_create(
        self, telegram_id: int, username: str | None, full_name: str
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
            )
            self.session.add(user)
            await self.session.flush()
        else:
            # به‌روزرسانی اطلاعات متغیر
            if user.username != username or user.full_name != full_name:
                user.username = username
                user.full_name = full_name
                await self.session.flush()
        return user

    async def set_ban(self, telegram_id: int, banned: bool) -> bool:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            return False
        user.is_banned = banned
        await self.session.commit()
        return True

    async def count(self) -> int:
        res = await self.session.execute(select(func.count(User.id)))
        return int(res.scalar_one())

    async def count_recent(self, hours: int = 24) -> int:
        since = utc_now().timestamp() - hours * 3600
        from datetime import datetime, timezone

        res = await self.session.execute(
            select(func.count(User.id)).where(
                User.created_at >= datetime.fromtimestamp(since, tz=timezone.utc)
            )
        )
        return int(res.scalar_one())

    async def all_ids(self, only_active: bool = True) -> list[int]:
        stmt = select(User.telegram_id)
        if only_active:
            stmt = stmt.where(User.is_banned.is_(False))
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def list_users(self, limit: int = 20) -> list[User]:
        res = await self.session.execute(
            select(User).order_by(User.id.desc()).limit(limit)
        )
        return list(res.scalars().all())

    async def unlock_password(self, telegram_id: int) -> None:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.unlocked_password = True
            await self.session.commit()
