"""
models/admin.py — Admin model.

Tracks bot administrators with permission levels.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base, TimestampMixin


class Admin(Base, TimestampMixin):
    """Bot administrator."""

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False,
        comment="Telegram user ID",
    )
    username: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Telegram username",
    )
    full_name: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Admin's full name",
    )
    is_main_admin: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="True only for the MAIN_ADMIN_ID (cannot be deleted)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Whether admin is currently active",
    )
    # Permissions (bit flags or simple booleans)
    can_upload: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Can upload files",
    )
    can_broadcast: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Can send broadcasts",
    )
    can_manage_users: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Can ban/unban users",
    )
    can_manage_settings: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Can change bot settings",
    )

    def __repr__(self) -> str:
        role = "MAIN" if self.is_main_admin else "ADMIN"
        return f"<Admin user_id={self.user_id} role={role}>"
