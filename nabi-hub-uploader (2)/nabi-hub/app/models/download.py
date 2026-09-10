"""مدل لاگ دانلود / Download log model."""
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IntIdMixin, TimestampMixin


class DownloadLog(Base, IntIdMixin, TimestampMixin):
    """ثبت هر بار دریافت فایل برای آمار."""

    __tablename__ = "download_logs"

    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    file_code: Mapped[Optional[str]] = mapped_column(
        String(32), index=True, nullable=True
    )
    file_id_ref: Mapped[Optional[int]] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"), nullable=True
    )
    ip_or_source: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    def __repr__(self) -> str:
        return f"<DownloadLog user={self.user_id} code={self.file_code}>"
