"""
services/file_service.py — File CRUD operations.
"""

from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.file import UploadedFile
from utils.deep_link import generate_file_token


class FileService:
    """Handles all file-related database operations."""

    @staticmethod
    async def create_file(
        session: AsyncSession,
        file_id: str,
        file_unique_id: str,
        file_type: str,
        uploader_id: int,
        file_name: Optional[str] = None,
        file_size: int = 0,
        mime_type: Optional[str] = None,
        caption: Optional[str] = None,
        album_id: Optional[str] = None,
        album_index: int = 0,
        album_caption: Optional[str] = None,
    ) -> UploadedFile:
        """Create a new file record and generate a deep link token."""
        token = generate_file_token(file_id=0, file_unique_id=file_unique_id)

        file_record = UploadedFile(
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_type=file_type,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            caption=caption,
            album_id=album_id,
            album_index=album_index,
            album_caption=album_caption,
            uploader_id=uploader_id,
            deep_link_token=token,
        )
        session.add(file_record)
        await session.commit()
        await session.refresh(file_record)

        logger.info(
            f"File created: id={file_record.id} type={file_type} "
            f"size={file_size} uploader={uploader_id}"
        )
        return file_record

    @staticmethod
    async def get_by_token(
        session: AsyncSession, token: str
    ) -> Optional[UploadedFile]:
        """Get file by deep link token."""
        stmt = select(UploadedFile).where(
            UploadedFile.deep_link_token == token,
            UploadedFile.is_public == True,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(
        session: AsyncSession, file_db_id: int
    ) -> Optional[UploadedFile]:
        """Get file by database ID."""
        stmt = select(UploadedFile).where(UploadedFile.id == file_db_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_album(
        session: AsyncSession, album_id: str
    ) -> list[UploadedFile]:
        """Get all files in an album, ordered by index."""
        stmt = (
            select(UploadedFile)
            .where(UploadedFile.album_id == album_id)
            .order_by(UploadedFile.album_index)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_all_files(
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UploadedFile]:
        """Get all files with pagination."""
        stmt = (
            select(UploadedFile)
            .order_by(UploadedFile.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_user_files(
        session: AsyncSession, uploader_id: int
    ) -> list[UploadedFile]:
        """Get all files uploaded by a specific user."""
        stmt = (
            select(UploadedFile)
            .where(UploadedFile.uploader_id == uploader_id)
            .order_by(UploadedFile.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_file(session: AsyncSession, file_db_id: int) -> bool:
        """Delete a file record."""
        stmt = delete(UploadedFile).where(UploadedFile.id == file_db_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @staticmethod
    async def increment_download(
        session: AsyncSession, file_db_id: int
    ) -> None:
        """Increment download counter for a file."""
        stmt = (
            update(UploadedFile)
            .where(UploadedFile.id == file_db_id)
            .values(download_count=UploadedFile.download_count + 1)
        )
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def count_files(session: AsyncSession) -> int:
        """Get total file count."""
        stmt = select(func.count()).select_from(UploadedFile)
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def count_total_downloads(session: AsyncSession) -> int:
        """Get total download count across all files."""
        stmt = select(func.coalesce(func.sum(UploadedFile.download_count), 0))
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def search_files(
        session: AsyncSession, query: str
    ) -> list[UploadedFile]:
        """Search files by name or token."""
        stmt = select(UploadedFile).where(
            (UploadedFile.file_name.ilike(f"%{query}%"))
            | (UploadedFile.deep_link_token.like(f"%{query}%"))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def set_channel_message(
        session: AsyncSession, file_db_id: int, channel_message_id: int
    ) -> None:
        """Record the channel message ID for a file."""
        stmt = (
            update(UploadedFile)
            .where(UploadedFile.id == file_db_id)
            .values(channel_message_id=channel_message_id)
        )
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    def generate_album_id() -> str:
        """Generate a unique album ID."""
        return str(uuid.uuid4())
