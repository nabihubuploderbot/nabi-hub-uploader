"""
models/file.py — Uploaded File model.

Stores metadata about files uploaded to the bot.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, String, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base, TimestampMixin


class UploadedFile(Base, TimestampMixin):
    """File uploaded through the bot."""

    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_unique_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="Telegram file_unique_id",
    )
    file_id: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Telegram file_id for sending",
    )
    file_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Type: document, photo, video, audio, voice, video_note",
    )
    file_name: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Original file name",
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger, default=0, comment="File size in bytes",
    )
    mime_type: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="MIME type",
    )
    caption: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="File caption (HTML)",
    )
    # Album support
    album_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True,
        comment="Album grouping ID for multi-file uploads",
    )
    album_index: Mapped[int] = mapped_column(
        Integer, default=0, comment="Index within album",
    )
    album_caption: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Shared album caption",
    )
    # Ownership
    uploader_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True,
        comment="User ID of the uploader",
    )
    # Status
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Whether file is accessible via deep link",
    )
    download_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="How many times this file was downloaded",
    )
    channel_message_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Message ID if forwarded to a channel",
    )
    # Deep link token (short unique code)
    deep_link_token: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True, index=True,
        comment="Short token for deep link: /start FILE_TOKEN",
    )

    def __repr__(self) -> str:
        return (
            f"<UploadedFile id={self.id} type={self.file_type} "
            f"size={self.file_size}>"
        )

    @property
    def human_size(self) -> str:
        """Human-readable file size."""
        size = self.file_size
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
