"""Base declarative model / مدل پایهٔ دکلراتیو."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """کلاس پایهٔ همهٔ مدل‌ها."""

    abstract = True


class TimestampMixin:
    """افزودن زمان ایجاد و به‌روزرسانی خودکار."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=None,
        onupdate=lambda: datetime.now(timezone.utc),
    )


class IntIdMixin:
    """کلید اصلی عددی خودافزا."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
