"""مدیریت پایگاه داده با SQLAlchemy 2.0 Async / Async database manager."""
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.base import Base


class Database:
    """مدیریت Engine و Session برای دسترسی Async به دیتابیس."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.engine: AsyncEngine = create_async_engine(url, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    async def create_all(self) -> None:
        """ایجاد خودکار همهٔ جداول در صورت نبود (Development)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        await self.engine.dispose()

    def session(self) -> AsyncSession:
        return self.session_factory()
