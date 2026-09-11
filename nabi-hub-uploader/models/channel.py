"""
models/channel.py — Force Join Channel model.

Stores channels that users must join before using the bot.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, String, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base, TimestampMixin


class ForceJoinChannel(Base, TimestampMixin):
    """A channel that requires mandatory subscription."""

    __tablename__ = "force_join_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False,
        comment="Telegram channel/chat ID (negative for channels)",
    )
    channel_username: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="Channel username (for public channels, without @)",
    )
    channel_title: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Channel display name",
    )
    invite_link: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Invite link for private channels",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Whether this lock is currently enforced",
    )
    priority: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="Display order priority (lower = shown first)",
    )

    def __repr__(self) -> str:
        return f"<ForceJoinChannel channel_id={self.channel_id} active={self.is_active}>"

    @property
    def display_name(self) -> str:
        """Return the best available display name."""
        return self.channel_title or self.channel_username or str(self.channel_id)

    @property
    def join_link(self) -> str:
        """Return a link users can click to join."""
        if self.channel_username:
            return f"https://t.me/{self.channel_username}"
        return self.invite_link or "#"
