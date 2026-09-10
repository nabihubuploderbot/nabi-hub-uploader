"""مدل آلبوم / Album model for group uploads."""
from typing import Optional

from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IntIdMixin, TimestampMixin


class Album(Base, IntIdMixin, TimestampMixin):
    """گروهی از فایل‌ها که با یک دیپ‌لینک واحد دسترسی می‌گیرند."""

    __tablename__ = "albums"

    album_code: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Album code={self.album_code}>"
