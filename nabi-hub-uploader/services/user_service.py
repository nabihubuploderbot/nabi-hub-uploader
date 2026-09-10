"""
services/user_service.py — User CRUD operations.
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.user import User


class UserService:
    """Handles all user-related database operations."""

    @staticmethod
    async def get_or_create(
        session: AsyncSession,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: str = "fa",
        is_premium: bool = False,
        referrer_id: Optional[int] = None,
    ) -> User:
        """
        Get an existing user or create a new one.
        Also updates user info on every interaction.
        """
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Update user info on each interaction
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.language_code = language_code
            user.is_premium = is_premium
            user.last_active = datetime.now(timezone.utc).isoformat()
        else:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
                is_premium=is_premium,
                referrer_id=referrer_id,
                last_active=datetime.now(timezone.utc).isoformat(),
            )
            session.add(user)
            logger.info(f"New user created: {user_id} (@{username})")

        await session.commit()
        return user

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by Telegram user_id."""
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(session: AsyncSession) -> list[User]:
        """Get all users."""
        stmt = select(User).order_by(User.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_active_user_ids(session: AsyncSession) -> list[int]:
        """Get all non-banned user IDs (for broadcast)."""
        stmt = select(User.user_id).where(User.is_banned == False)
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]

    @staticmethod
    async def ban_user(session: AsyncSession, user_id: int) -> bool:
        """Ban a user."""
        stmt = update(User).where(User.user_id == user_id).values(is_banned=True)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @staticmethod
    async def unban_user(session: AsyncSession, user_id: int) -> bool:
        """Unban a user."""
        stmt = update(User).where(User.user_id == user_id).values(is_banned=False)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @staticmethod
    async def increment_downloads(session: AsyncSession, user_id: int) -> None:
        """Increment download counter for a user."""
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(download_count=User.download_count + 1)
        )
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def set_force_join_passed(
        session: AsyncSession, user_id: int, passed: bool
    ) -> None:
        """Update force join status for a user."""
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(force_join_passed=passed)
        )
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def set_reaction_passed(
        session: AsyncSession, user_id: int, passed: bool
    ) -> None:
        """Update reaction lock status for a user."""
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(reaction_passed=passed)
        )
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def count_users(session: AsyncSession) -> int:
        """Get total user count."""
        stmt = select(func.count()).select_from(User)
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def count_banned(session: AsyncSession) -> int:
        """Get banned user count."""
        stmt = select(func.count()).select_from(User).where(User.is_banned == True)
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def search_user(
        session: AsyncSession, query: str
    ) -> list[User]:
        """Search users by user_id or username."""
        stmt = select(User).where(
            (User.user_id.cast(str).like(f"%{query}%"))
            | (User.username.ilike(f"%{query}%"))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
