"""مدل قفل واکنش / Reaction lock model."""
from typing import Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IntIdMixin, TimestampMixin


class ReactionLock(Base, IntIdMixin, TimestampMixin):
    """پست هدف برای قفل واکنش؛ کاربر باید روی آن ری‌اکشن بزند."""

    __tablename__ = "reaction_locks"

    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    # ایموجی الزامی (مثلاً 👍) - خالی = هر واکنشی
    required_emoji: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<ReactionLock chat={self.chat_id} msg={self.message_id}>"
