"""
services/setting_service.py — Bot settings management.
"""

from __future__ import annotations

from typing import Optional, Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.setting import BotSetting, SettingKeys


class SettingService:
    """Manages bot settings stored in the database."""

    @staticmethod
    async def get(
        session: AsyncSession,
        key: str,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """Get a setting value by key."""
        stmt = select(BotSetting).where(BotSetting.key == key)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        return setting.value if setting else default

    @staticmethod
    async def get_bool(
        session: AsyncSession, key: str, default: bool = False
    ) -> bool:
        """Get a boolean setting."""
        value = await SettingService.get(session, key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes")

    @staticmethod
    async def get_int(
        session: AsyncSession, key: str, default: int = 0
    ) -> int:
        """Get an integer setting."""
        value = await SettingService.get(session, key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    @staticmethod
    async def set(
        session: AsyncSession,
        key: str,
        value: Any,
        value_type: str = "str",
    ) -> None:
        """Set or update a setting."""
        stmt = select(BotSetting).where(BotSetting.key == key)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()

        str_value = str(value) if value is not None else None

        if setting:
            setting.value = str_value
            setting.value_type = value_type
        else:
            setting = BotSetting(
                key=key,
                value=str_value,
                value_type=value_type,
            )
            session.add(setting)

        await session.commit()
        logger.debug(f"Setting updated: {key} = {str_value}")

    @staticmethod
    async def delete(session: AsyncSession, key: str) -> bool:
        """Delete a setting."""
        stmt = select(BotSetting).where(BotSetting.key == key)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        if setting:
            await session.delete(setting)
            await session.commit()
            return True
        return False

    @staticmethod
    async def get_all(session: AsyncSession) -> list[BotSetting]:
        """Get all settings."""
        stmt = select(BotSetting).order_by(BotSetting.key)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def init_defaults(session: AsyncSession) -> None:
        """Initialize default settings if they don't exist."""
        defaults = {
            SettingKeys.BOT_ENABLED: ("true", "bool"),
            SettingKeys.WELCOME_MESSAGE: (
                "👋 به ربات **Nabi Hub | Uploader** خوش آمدید!\n\n"
                "برای دریافت فایل، لینک عمیق مربوطه را ارسال کنید.",
                "str",
            ),
            SettingKeys.FORCE_JOIN_MESSAGE: (
                "⚠️ برای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید:",
                "str",
            ),
            SettingKeys.REACTION_LOCK_MESSAGE: (
                "❤️ لطفاً روی پست مشخص‌شده در کانال واکنش بگذارید.",
                "str",
            ),
            SettingKeys.DELAY_BEFORE_SEND: ("0", "int"),
            SettingKeys.SHOW_BUTTONS: ("true", "bool"),
        }

        for key, (value, vtype) in defaults.items():
            existing = await SettingService.get(session, key)
            if existing is None:
                await SettingService.set(session, key, value, vtype)

        logger.info("Default settings initialized")
