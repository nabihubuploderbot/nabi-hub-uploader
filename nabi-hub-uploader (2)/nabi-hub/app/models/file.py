"""مدل فایل آپلودشده / Uploaded file model."""
from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IntIdMixin, TimestampMixin


class File(Base, IntIdMixin, TimestampMixin):
    """هر فایلی که کاربر/ادمین آپلود می‌کند با شناسهٔ یکتا برای دیپ‌لینک."""

    __tablename__ = "files"

    # شناسهٔ یکتای متنی برای /start {file_code}
    file_code: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    telegram_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), default="document")
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # آلبوم مرتبط (nullable)
    album_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("albums.id", ondelete="SET NULL"), nullable=True
    )
    owner_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    is_protected: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_password: Mapped[bool] = mapped_column(Boolean, default=False)
    password: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    download_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<File code={self.file_code} type={self.file_type}>"
