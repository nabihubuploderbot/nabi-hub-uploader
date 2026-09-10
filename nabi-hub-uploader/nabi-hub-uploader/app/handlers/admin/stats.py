"""آمار ربات / Statistics handler."""
from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.core.db import Database
from app.keyboards.admin_panel import main_panel_keyboard
from app.locales.fa import TEXTS
from app.services.stats_service import gather_stats

router = Router(name="admin_stats")


@router.callback_query(F.data == "stats:show")
async def cb_stats(cb: CallbackQuery, db: Database) -> None:
    """نمایش آمار کامل / Show full statistics."""
    async with db.session_factory() as session:
        stats = await gather_stats(session)
    await cb.message.edit_text(
        TEXTS["stats"].format(**stats),
        reply_markup=main_panel_keyboard(),
    )
    await cb.answer()
