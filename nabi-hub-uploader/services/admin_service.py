"""
services/admin_service.py — Admin management operations.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.admin import Admin


class AdminService:
    """Handles admin CRUD operations."""

    @staticmethod
    async def get_or_create_main_admin(
        session: AsyncSession,
        user_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> Admin:
        """Ensure the main admin exists in the database."""
        stmt = select(Admin).where(Admin.user_id == user_id)
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()

        if not admin:
            admin = Admin(
                user_id=user_id,
                username=username,
                full_name=full_name,
                is_main_admin=True,
                is_active=True,
                can_upload=True,
                can_broadcast=True,
                can_manage_users=True,
                can_manage_settings=True,
            )
            session.add(admin)
            await session.commit()
            logger.info(f"Main admin registered: {user_id}")
        return admin

    @staticmethod
    async def add_admin(
        session: AsyncSession,
        user_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> Admin:
        """Add a new admin."""
        stmt = select(Admin).where(Admin.user_id == user_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.is_active = True
            await session.commit()
            return existing

        admin = Admin(
            user_id=user_id,
            username=username,
            full_name=full_name,
            is_main_admin=False,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        logger.info(f"New admin added: {user_id}")
        return admin

    @staticmethod
    async def remove_admin(session: AsyncSession, user_id: int) -> bool:
        """Remove an admin (cannot remove main admin)."""
        stmt = select(Admin).where(Admin.user_id == user_id)
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()

        if not admin or admin.is_main_admin:
            return False

        await session.delete(admin)
        await session.commit()
        logger.info(f"Admin removed: {user_id}")
        return True

    @staticmethod
    async def is_admin(session: AsyncSession, user_id: int) -> bool:
        """Check if a user is an active admin."""
        stmt = select(Admin).where(
            Admin.user_id == user_id,
            Admin.is_active == True,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def is_main_admin(session: AsyncSession, user_id: int) -> bool:
        """Check if a user is the main admin."""
        stmt = select(Admin).where(
            Admin.user_id == user_id,
            Admin.is_main_admin == True,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_admin(session: AsyncSession, user_id: int) -> Optional[Admin]:
        """Get admin by user_id."""
        stmt = select(Admin).where(Admin.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_admins(session: AsyncSession) -> list[Admin]:
        """Get all active admins."""
        stmt = select(Admin).where(Admin.is_active == True).order_by(
            Admin.is_main_admin.desc(),
            Admin.created_at,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def count_admins(session: AsyncSession) -> int:
        """Get total active admin count."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(Admin).where(Admin.is_active == True)
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def update_permissions(
        session: AsyncSession,
        user_id: int,
        **permissions: bool,
    ) -> bool:
        """Update admin permissions."""
        stmt = (
            update(Admin)
            .where(Admin.user_id == user_id, Admin.is_main_admin == False)
            .values(**permissions)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
