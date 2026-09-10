"""سرویس آمار / Stats service."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album
from app.models.download import DownloadLog
from app.models.file import File
from app.models.user import User
from app.services.admin_service import AdminService
from app.services.user_service import UserService


async def gather_stats(session: AsyncSession) -> dict[str, int]:
    """جمع‌آوری آمار کامل ربات."""
    users = await session.execute(select(func.count(User.id)))
    files = await session.execute(select(func.count(File.id)))
    albums = await session.execute(select(func.count(Album.id)))
    downloads = await session.execute(select(func.count(DownloadLog.id)))
    recent = await UserService(session).count_recent(24)
    admins = await AdminService(session).count()
    return {
        "users": int(users.scalar_one()),
        "files": int(files.scalar_one()),
        "albums": int(albums.scalar_one()),
        "downloads": int(downloads.scalar_one()),
        "recent": int(recent),
        "admins": int(admins),
    }
