"""مدل ادمین / Admin model."""
from typing import Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IntIdMixin, TimestampMixin


class Admin(Base, IntIdMixin, TimestampMixin):
    """ادمین‌های ربات؛ ادمین اصلی حذف‌نشدنی است."""

    __tablename__ = "admins"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Admin tg={self.telegram_id} main={self.is_main}>"
