"""
models/broadcast.py — Broadcast Log model.

Tracks broadcast messages sent to users.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, String, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base, TimestampMixin


class BroadcastLog(Base, TimestampMixin):
    """Log entry for a broadcast message."""

    __tablename__ = "broadcast_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Admin who initiated the broadcast",
    )
    message_text: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Broadcast message text or caption",
    )
    media_file_id: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="File ID if broadcast includes media",
    )
    media_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="Media type: photo, video, document, etc.",
    )
    is_forward: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="True if this was a forward (not a new message)",
    )
    source_chat_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True,
        comment="Source chat ID for forwards",
    )
    source_message_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Source message ID for forwards",
    )
    total_users: Mapped[int] = mapped_column(
        Integer, default=0, comment="Total target users",
    )
    success_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Successfully sent count",
    )
    fail_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Failed delivery count",
    )
    block_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Users who blocked the bot",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending",
        comment="Status: pending, running, completed, cancelled",
    )

    def __repr__(self) -> str:
        return (
            f"<BroadcastLog id={self.id} status={self.status} "
            f"success={self.success_count}/{self.total_users}>"
        )

    @property
    def progress_percent(self) -> float:
        processed = self.success_count + self.fail_count + self.block_count
        if self.total_users == 0:
            return 0.0
        return (processed / self.total_users) * 100
