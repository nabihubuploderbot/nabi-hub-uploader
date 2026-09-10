"""
models/user.py — Telegram User model.

Stores user information, interaction counts, and subscription status.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, String, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Telegram user record."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False,
        comment="Telegram user ID",
    )
    username: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Telegram username",
    )
    first_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="User first name",
    )
    last_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="User last name",
    )
    language_code: Mapped[str] = mapped_column(
        String(10), default="fa", comment="User language code",
    )
    is_banned: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether user is banned",
    )
    is_premium: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Telegram Premium user",
    )
    download_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Total file downloads",
    )
    last_active: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Last activity timestamp",
    )
    referrer_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="Referrer user ID (deep link)",
    )
    force_join_passed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Passed force join check",
    )
    reaction_passed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Passed reaction lock check",
    )
    extra_data: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON extra data",
    )

    # ── Relationships ────────────────────────────────
    # files = relationship("UploadedFile", back_populates="uploader", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User user_id={self.user_id} username={self.username}>"

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(parts).strip() or str(self.user_id)

    @property
    def mention(self) -> str:
        """Return a mention link for the user."""
        if self.username:
            return f"@{self.username}"
        return f"<a href='tg://user?id={self.user_id}'>{self.full_name}</a>"
