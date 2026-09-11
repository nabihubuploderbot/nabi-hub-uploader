"""
models/setting.py — Bot Settings model.

Key-value store for all configurable bot settings.
"""

from __future__ import annotations

from sqlalchemy import String, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base, TimestampMixin


class BotSetting(Base, TimestampMixin):
    """A single bot configuration setting."""

    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="Setting key (e.g., 'welcome_message', 'bot_enabled')",
    )
    value: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Setting value (stored as text, cast as needed)",
    )
    value_type: Mapped[str] = mapped_column(
        String(20), default="str",
        comment="Data type: str, int, bool, json",
    )

    def __repr__(self) -> str:
        return f"<BotSetting key={self.key} value={self.value}>"

    def as_bool(self) -> bool:
        return self.value.lower() in ("true", "1", "yes") if self.value else False

    def as_int(self) -> int:
        return int(self.value) if self.value else 0


# ── Default Settings Keys ───────────────────────────
class SettingKeys:
    """Constants for all setting keys used in the bot."""

    BOT_ENABLED = "bot_enabled"
    WELCOME_MESSAGE = "welcome_message"
    FORCE_JOIN_MESSAGE = "force_join_message"
    REACTION_LOCK_MESSAGE = "reaction_lock_message"
    FILE_CAPTION = "file_caption"
    ALBUM_CAPTION = "album_caption"
    DELAY_BEFORE_SEND = "delay_before_send"
    PASSWORD = "access_password"
    CHANNEL_USERNAME = "channel_username"
    FORWARD_CHANNEL_ID = "forward_channel_id"
    SHOW_BUTTONS = "show_buttons"
    BUTTON_TEXT = "button_text"
    BUTTON_URL = "button_url"
    START_PHOTO_URL = "start_photo_url"
    DONE_BUTTON_TEXT = "done_button_text"
