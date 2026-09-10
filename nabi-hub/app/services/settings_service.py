"""سرویس تنظیمات / Settings service (single global row + key-value rows)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import BotSettings

GLOBAL_KEY = "global"


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self) -> BotSettings:
        """ردیف تنظیمات سراسری را می‌گیرد یا می‌سازد."""
        res = await self.session.execute(
            select(BotSettings).where(BotSettings.key == GLOBAL_KEY)
        )
        settings = res.scalar_one_or_none()
        if settings is None:
            settings = BotSettings(key=GLOBAL_KEY)
            self.session.add(settings)
            await self.session.commit()
        return settings

    async def save(self, settings: BotSettings) -> None:
        await self.session.commit()

    # ── Key-Value عمومی ──
    async def get_kv(self, key: str) -> str | None:
        res = await self.session.execute(
            select(BotSettings).where(BotSettings.key == key)
        )
        row = res.scalar_one_or_none()
        return row.value if row else None

    async def set_kv(self, key: str, value: str | None) -> None:
        res = await self.session.execute(
            select(BotSettings).where(BotSettings.key == key)
        )
        row = res.scalar_one_or_none()
        if row is None:
            row = BotSettings(key=key, value=value)
            self.session.add(row)
        else:
            row.value = value
        await self.session.commit()
