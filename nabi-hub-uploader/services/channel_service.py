"""
services/channel_service.py — Channel lock management.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.channel import ForceJoinChannel
from models.reaction_lock import ReactionLock


class ChannelService:
    """Handles force-join channel and reaction lock operations."""

    # ── Force Join Channels ──────────────────────────

    @staticmethod
    async def add_channel(
        session: AsyncSession,
        channel_id: int,
        channel_username: Optional[str] = None,
        channel_title: Optional[str] = None,
        invite_link: Optional[str] = None,
    ) -> ForceJoinChannel:
        """Add a new force-join channel."""
        stmt = select(ForceJoinChannel).where(
            ForceJoinChannel.channel_id == channel_id
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.is_active = True
            existing.channel_username = channel_username
            existing.channel_title = channel_title
            if invite_link:
                existing.invite_link = invite_link
            await session.commit()
            return existing

        channel = ForceJoinChannel(
            channel_id=channel_id,
            channel_username=channel_username,
            channel_title=channel_title,
            invite_link=invite_link,
            is_active=True,
        )
        session.add(channel)
        await session.commit()
        logger.info(f"Force-join channel added: {channel_id}")
        return channel

    @staticmethod
    async def remove_channel(session: AsyncSession, channel_id: int) -> bool:
        """Remove a force-join channel."""
        stmt = delete(ForceJoinChannel).where(
            ForceJoinChannel.channel_id == channel_id
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @staticmethod
    async def toggle_channel(
        session: AsyncSession, channel_id: int
    ) -> Optional[bool]:
        """Toggle active state of a channel. Returns new state."""
        stmt = select(ForceJoinChannel).where(
            ForceJoinChannel.channel_id == channel_id
        )
        result = await session.execute(stmt)
        channel = result.scalar_one_or_none()
        if not channel:
            return None
        channel.is_active = not channel.is_active
        await session.commit()
        return channel.is_active

    @staticmethod
    async def get_active_channels(
        session: AsyncSession,
    ) -> list[ForceJoinChannel]:
        """Get all active force-join channels."""
        stmt = (
            select(ForceJoinChannel)
            .where(ForceJoinChannel.is_active == True)
            .order_by(ForceJoinChannel.priority)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_all_channels(
        session: AsyncSession,
    ) -> list[ForceJoinChannel]:
        """Get all force-join channels."""
        stmt = select(ForceJoinChannel).order_by(ForceJoinChannel.priority)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def count_channels(session: AsyncSession) -> int:
        """Count active force-join channels."""
        stmt = (
            select(func.count())
            .select_from(ForceJoinChannel)
            .where(ForceJoinChannel.is_active == True)
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    # ── Reaction Locks ───────────────────────────────

    @staticmethod
    async def add_reaction_lock(
        session: AsyncSession,
        channel_id: int,
        message_id: int,
        reaction_emoji: Optional[str] = None,
    ) -> ReactionLock:
        """Add a new reaction lock."""
        lock = ReactionLock(
            channel_id=channel_id,
            message_id=message_id,
            reaction_emoji=reaction_emoji,
            is_active=True,
        )
        session.add(lock)
        await session.commit()
        logger.info(f"Reaction lock added: ch={channel_id} msg={message_id}")
        return lock

    @staticmethod
    async def remove_reaction_lock(
        session: AsyncSession, lock_id: int
    ) -> bool:
        """Remove a reaction lock."""
        stmt = delete(ReactionLock).where(ReactionLock.id == lock_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @staticmethod
    async def get_active_reaction_locks(
        session: AsyncSession,
    ) -> list[ReactionLock]:
        """Get all active reaction locks."""
        stmt = select(ReactionLock).where(ReactionLock.is_active == True)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_all_reaction_locks(
        session: AsyncSession,
    ) -> list[ReactionLock]:
        """Get all reaction locks."""
        stmt = select(ReactionLock).order_by(ReactionLock.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
