"""سرویس قفل‌ها (جوین اجباری + واکنش) / Locks service."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel
from app.models.reaction import ReactionLock


class LockService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── کانال‌های جوین اجباری ──
    async def get_active_channels(self) -> list[Channel]:
        res = await self.session.execute(
            select(Channel).where(Channel.is_active.is_(True)).order_by(Channel.position)
        )
        return list(res.scalars().all())

    async def get_all_channels(self) -> list[Channel]:
        res = await self.session.execute(select(Channel).order_by(Channel.position))
        return list(res.scalars().all())

    async def add_channel(
        self,
        chat_id: int,
        title: str | None = None,
        username: str | None = None,
        invite_link: str | None = None,
    ) -> Channel:
        channel = Channel(
            chat_id=chat_id,
            title=title,
            username=username,
            invite_link=invite_link,
            position=0,
        )
        self.session.add(channel)
        await self.session.commit()
        return channel

    async def remove_channel(self, channel_id: int) -> bool:
        res = await self.session.execute(select(Channel).where(Channel.id == channel_id))
        ch = res.scalar_one_or_none()
        if ch is None:
            return False
        await self.session.delete(ch)
        await self.session.commit()
        return True

    async def find_channel_by_chat_id(self, chat_id: int) -> Channel | None:
        res = await self.session.execute(
            select(Channel).where(Channel.chat_id == chat_id)
        )
        return res.scalar_one_or_none()

    # ── قفل واکنش ──
    async def get_active_reaction_lock(self) -> ReactionLock | None:
        res = await self.session.execute(
            select(ReactionLock).where(ReactionLock.is_active.is_(True))
        )
        return res.scalar_one_or_none()

    async def set_reaction_lock(
        self, chat_id: int, message_id: int, required_emoji: str | None = None
    ) -> ReactionLock:
        # قفل قبلی غیرفعال می‌شود (فقط یک قفل فعال)
        old = await self.get_active_reaction_lock()
        if old:
            old.is_active = False
        lock = ReactionLock(
            chat_id=chat_id,
            message_id=message_id,
            required_emoji=required_emoji,
            is_active=True,
        )
        self.session.add(lock)
        await self.session.commit()
        return lock

    async def deactivate_reaction_lock(self) -> bool:
        lock = await self.get_active_reaction_lock()
        if lock is None:
            return False
        lock.is_active = False
        await self.session.commit()
        return True
