"""مدل کانال‌های قفل عضویت / Force-join channels model."""
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IntIdMixin, TimestampMixin


class Channel(Base, IntIdMixin, TimestampMixin):
    """کانال‌های عمومی/خصوصی برای جوین اجباری."""

    __tablename__ = "channels"

    chat_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    invite_link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # ترتیب نمایش
    position: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<Channel chat={self.chat_id} title={self.title}>"
