"""سرویس فایل و آلبوم / File & album service."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album
from app.models.file import File
from app.utils.helpers import generate_code


class FileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_file(
        self,
        *,
        telegram_file_id: str,
        file_type: str,
        file_size: int = 0,
        file_name: str | None = None,
        caption: str | None = None,
        album_id: int | None = None,
        owner_id: int | None = None,
        needs_password: bool = False,
        password: str | None = None,
        file_code: str | None = None,
    ) -> File:
        file = File(
            file_code=file_code or generate_code(),
            telegram_file_id=telegram_file_id,
            file_type=file_type,
            file_size=file_size,
            file_name=file_name,
            caption=caption,
            album_id=album_id,
            owner_id=owner_id,
            needs_password=needs_password,
            password=password,
        )
        self.session.add(file)
        await self.session.commit()
        return file

    async def get_by_code(self, code: str) -> File | None:
        res = await self.session.execute(
            select(File).where(File.file_code == code)
        )
        return res.scalar_one_or_none()

    async def delete_by_code(self, code: str) -> bool:
        file = await self.get_by_code(code)
        if file is None:
            return False
        await self.session.delete(file)
        await self.session.commit()
        return True

    async def count(self) -> int:
        res = await self.session.execute(select(func.count(File.id)))
        return int(res.scalar_one())

    async def inc_download(self, file_id: int) -> None:
        res = await self.session.execute(
            select(File).where(File.id == file_id)
        )
        file = res.scalar_one_or_none()
        if file:
            file.download_count += 1
            await self.session.commit()

    # ── آلبوم‌ها ──
    async def create_album(
        self,
        *,
        title: str | None = None,
        caption: str | None = None,
        owner_id: int | None = None,
    ) -> Album:
        album = Album(
            album_code=generate_code(),
            title=title,
            caption=caption,
            owner_id=owner_id,
        )
        self.session.add(album)
        await self.session.commit()
        return album

    async def get_album_by_code(self, code: str) -> Album | None:
        res = await self.session.execute(
            select(Album).where(Album.album_code == code)
        )
        return res.scalar_one_or_none()

    async def album_files(self, album_id: int) -> list[File]:
        res = await self.session.execute(
            select(File)
            .where(File.album_id == album_id)
            .order_by(File.id)
        )
        return list(res.scalars().all())

    async def count_albums(self) -> int:
        res = await self.session.execute(select(func.count(Album.id)))
        return int(res.scalar_one())
