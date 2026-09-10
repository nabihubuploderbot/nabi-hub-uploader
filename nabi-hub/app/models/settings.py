"""مدل تنظیمات ربات / Bot settings model (single-row key-value style)."""
from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IntIdMixin, TimestampMixin


class BotSettings(Base, IntIdMixin, TimestampMixin):
    """تنظیمات سراسری؛ هر ردیف یک کلید/مقدار."""

    __tablename__ = "bot_settings"

    key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # پرچم‌های پرکاربرد به‌صورت ستون برای سرعت
    bot_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    send_to_channel: Mapped[bool] = mapped_column(Boolean, default=False)
    force_join_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reaction_lock_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    forward_lock_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    timer_seconds: Mapped[int] = mapped_column(Integer, default=0)
    global_password: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    channel_log_id: Mapped[Optional[int]] = mapped_column(String(64), nullable=True)
    group_id: Mapped[Optional[int]] = mapped_column(String(64), nullable=True)
    default_caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lock_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<BotSettings key={self.key}>"
