"""
models/reaction_lock.py — Reaction Lock model.

Stores posts where users must react before accessing files.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base, TimestampMixin


class ReactionLock(Base, TimestampMixin):
    """A specific post that requires a reaction before access."""

    __tablename__ = "reaction_locks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True,
        comment="Channel ID where the post exists",
    )
    message_id: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Message ID in the channel to react to",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Whether this reaction lock is enforced",
    )
    reaction_emoji: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Required emoji reaction (null = any reaction accepted)",
    )

    def __repr__(self) -> str:
        return (
            f"<ReactionLock channel={self.channel_id} "
            f"msg={self.message_id} active={self.is_active}>"
        )
