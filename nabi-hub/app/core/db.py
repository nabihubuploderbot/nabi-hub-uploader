"""مدیریت پایگاه داده با SQLAlchemy 2.0 Async / Async database manager."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.base import Base


def normalize_async_url(url: str) -> str:
    """نرمال‌سازی URL دیتابیس به فرمت Async / Normalize DB URL to async driver form.

    Railway متغیر DATABASE_URL را به‌صورت postgresql://... می‌دهد که برای
    SQLAlchemy Async معتبر نیست و برنامه در لحظهٔ استارت کرش می‌کند.
    این تابع به‌طور خودکار درایور asyncpg را اضافه می‌کند.
    """
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


class Database:
    """مدیریت Engine و Session برای دسترسی Async به دیتابیس."""

    def __init__(self, url: str) -> None:
        self.url = normalize_async_url(url)
        self.engine: AsyncEngine = create_async_engine(self.url, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    async def create_all(self) -> None:
        """ایجاد خودکار همهٔ جداول در صورت نبود (Development)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def check(self) -> None:
        """تست اتصال ساده / Simple connectivity check."""
        async with self.engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

    async def close(self) -> None:
        await self.engine.dispose()

    def session(self) -> AsyncSession:
        return self.session_factory()
