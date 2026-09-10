"""مدل کاربر / User model."""
from typing import Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IntIdMixin, TimestampMixin


class User(Base, IntIdMixin, TimestampMixin):
    """کاربران ربات + وضعیت قفل‌ها و دسترسی."""

    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    lang: Mapped[str] = mapped_column(String(8), default="fa")

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    # وضعیت چک‌های اجباری
    joined_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    reacted_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    # دسترسی پسورددار
    unlocked_password: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id}>"
