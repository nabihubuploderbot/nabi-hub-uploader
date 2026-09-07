"""
admin_manage.py — مدیریت ادمین‌ها

همه پیام‌ها دکمه اینلاین دارن ✅
"""

from __future__ import annotations

from typing import Callable

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings as app_settings
from services.admin_service import AdminService
from keyboards.inline import CD, panel_button, settings_button, cancel_panel_button

router = Router(name="admin_manage")


class AdminManageStates(StatesGroup):
    waiting_admin_id_add = State()
    waiting_admin_id_remove = State()


def _admin_management_keyboard():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ افزودن ادمین", callback_data="adm_add"),
        InlineKeyboardButton(text="➖ حذف ادمین", callback_data="adm_remove"),
    )
    builder.row(
        InlineKeyboardButton(text="📋 لیست ادمین‌ها", callback_data="adm_list"),
        InlineKeyboardButton(text="🔑 تنظیم دسترسی‌ها", callback_data="adm_perms"),
    )
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADMIN_SETTINGS))
    return builder.as_markup()


@router.callback_query(F.data == CD.ADV_ADMIN_MGMT)
async def show_admin_management_menu(callback: CallbackQuery, is_admin: bool, is_main_admin: bool) -> None:
    if not is_main_admin:
        await callback.answer("⛔ فقط ادمین اصلی", show_alert=True)
        return
    await callback.message.edit_text(
        "👑 **مدیریت ادمین‌ها**\n\nاز منوی زیر عمل مورد نظر را انتخاب کنید:",
        reply_markup=_admin_management_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "adm_add")
async def start_add_admin(callback: CallbackQuery, state: FSMContext, is_main_admin: bool) -> None:
    if not is_main_admin:
        await callback.answer("⛔ فقط ادمین اصلی", show_alert=True)
        return
    await state.set_state(AdminManageStates.waiting_admin_id_add)
    await callback.message.edit_text(
        "➕ **افزودن ادمین جدید**\n\nآیدی عددی کاربر را وارد کنید:\n\n💡 کاربر باید ابتدا /start زده باشد.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(AdminManageStates.waiting_admin_id_add)
async def process_add_admin(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    text = message.text.strip()
    try:
        user_id = int(text)
    except ValueError:
        await message.answer(
            "⚠️ **آیدی نامعتبر!**\n\nلطفاً یک عدد صحیح وارد کنید.",
            parse_mode="Markdown",
            reply_markup=cancel_panel_button(),
        )
        return
    try:
        user_chat = await bot.get_chat(user_id)
        full_name = user_chat.first_name or ""
        if user_chat.last_name:
            full_name += " " + user_chat.last_name
        username = user_chat.username
    except Exception:
        full_name = None
        username = None
    admin = await AdminService.add_admin(session=session, user_id=user_id, username=username, full_name=full_name)
    await state.clear()
    await message.answer(
        f"✅ **ادمین جدید اضافه شد!**\n\n"
        f"👤 آیدی: `{user_id}`\n"
        f"📝 نام: {full_name or 'نامشخص'}\n"
        f"🔗 یوزرنیم: @{username or 'ندارد'}\n\n"
        f"دسترسی‌های پیش‌فرض:\n"
        f"📤 آپلود: ✅ | 📢 ارسال: ❌\n"
        f"👥 کاربران: ❌ | ⚙️ تنظیمات: ❌",
        parse_mode="Markdown",
        reply_markup=_admin_management_keyboard(),
    )
    logger.info(f"New admin added: {user_id} by {message.from_user.id}")


@router.callback_query(F.data == "adm_remove")
async def show_remove_admin_list(callback: CallbackQuery, session: AsyncSession, is_main_admin: bool) -> None:
    if not is_main_admin:
        await callback.answer("⛔ فقط ادمین اصلی", show_alert=True)
        return
    admins = await AdminService.get_all_admins(session)
    removable = [a for a in admins if not a.is_main_admin]
    if not removable:
        await callback.answer("⚠️ ادمین دیگری برای حذف وجود ندارد.", show_alert=True)
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    for admin in removable:
        name = admin.full_name or str(admin.user_id)
        builder.row(InlineKeyboardButton(text=f"🗑 {name} (`{admin.user_id}`)", callback_data=f"adm_rm_confirm:{admin.user_id}"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm_menu_back"))
    await callback.message.edit_text("➖ **حذف ادمین**\n\nادمین مورد نظر را انتخاب کنید:", reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("adm_rm_confirm:"))
async def confirm_remove_admin(callback: CallbackQuery, session: AsyncSession, is_main_admin: bool) -> None:
    if not is_main_admin:
        return
    user_id = int(callback.data.split(":")[1])
    removed = await AdminService.remove_admin(session, user_id)
    if removed:
        await callback.answer(f"✅ ادمین {user_id} حذف شد.", show_alert=True)
    else:
        await callback.answer("⚠️ ادمین یافت نشد.", show_alert=True)
    await show_remove_admin_list(callback, session, is_main_admin)


@router.callback_query(F.data == "adm_list")
async def show_admin_list(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    if not is_admin:
        return
    admins = await AdminService.get_all_admins(session)
    text = "👑 **لیست ادمین‌ها:**\n\n"
    for i, admin in enumerate(admins, 1):
        role = "⭐ اصلی" if admin.is_main_admin else "👤"
        name = admin.full_name or "نامشخص"
        perms = []
        if admin.can_upload:
            perms.append("📤")
        if admin.can_broadcast:
            perms.append("📢")
        if admin.can_manage_users:
            perms.append("👥")
        if admin.can_manage_settings:
            perms.append("⚙️")
        text += f"**{i}. {role}**\n   👤 {name}\n   🆔 `{admin.user_id}`\n   🔑 {'|'.join(perms) or 'هیچ'}\n\n"
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm_menu_back"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "adm_perms")
async def show_perms_admin_list(callback: CallbackQuery, session: AsyncSession, is_main_admin: bool) -> None:
    if not is_main_admin:
        await callback.answer("⛔ فقط ادمین اصلی", show_alert=True)
        return
    admins = await AdminService.get_all_admins(session)
    editable = [a for a in admins if not a.is_main_admin]
    if not editable:
        await callback.answer("⚠️ ادمین دیگری وجود ندارد.", show_alert=True)
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    for admin in editable:
        name = admin.full_name or str(admin.user_id)
        builder.row(InlineKeyboardButton(text=f"🔑 {name} (`{admin.user_id}`)", callback_data=f"adm_perms_edit:{admin.user_id}"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm_menu_back"))
    await callback.message.edit_text("🔑 **تنظیم دسترسی‌ها**\n\nادمین مورد نظر:", reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("adm_perms_edit:"))
async def edit_admin_permissions(callback: CallbackQuery, session: AsyncSession, is_main_admin: bool) -> None:
    if not is_main_admin:
        return
    user_id = int(callback.data.split(":")[1])
    admin = await AdminService.get_admin(session, user_id)
    if not admin:
        await callback.answer("⚠️ ادمین یافت نشد.", show_alert=True)
        return
    name = admin.full_name or str(admin.user_id)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f"{'✅' if admin.can_upload else '❌'} 📤 آپلود فایل", callback_data=f"adm_perm_toggle:{user_id}:upload"))
    builder.row(InlineKeyboardButton(text=f"{'✅' if admin.can_broadcast else '❌'} 📢 ارسال همگانی", callback_data=f"adm_perm_toggle:{user_id}:broadcast"))
    builder.row(InlineKeyboardButton(text=f"{'✅' if admin.can_manage_users else '❌'} 👥 مدیریت کاربران", callback_data=f"adm_perm_toggle:{user_id}:users"))
    builder.row(InlineKeyboardButton(text=f"{'✅' if admin.can_manage_settings else '❌'} ⚙️ مدیریت تنظیمات", callback_data=f"adm_perm_toggle:{user_id}:settings"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="adm_perms"))
    await callback.message.edit_text(
        f"🔑 **دسترسی‌های ادمین:**\n\n👤 {name}\n🆔 `{user_id}`\n\nهر دسترسی را toggle کنید:",
        reply_markup=builder.as_markup(), parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_perm_toggle:"))
async def toggle_admin_permission(callback: CallbackQuery, session: AsyncSession, is_main_admin: bool) -> None:
    if not is_main_admin:
        return
    parts = callback.data.split(":")
    user_id = int(parts[1])
    perm_key = parts[2]
    admin = await AdminService.get_admin(session, user_id)
    if not admin:
        await callback.answer("⚠️ ادمین یافت نشد.", show_alert=True)
        return
    perm_map = {"upload": "can_upload", "broadcast": "can_broadcast", "users": "can_manage_users", "settings": "can_manage_settings"}
    if perm_key in perm_map:
        field = perm_map[perm_key]
        current_value = getattr(admin, field)
        await AdminService.update_permissions(session, user_id, **{field: not current_value})
        await callback.answer("✅ تغییر کرد.")
    await edit_admin_permissions(callback, session, is_main_admin)


@router.callback_query(F.data == "adm_menu_back")
async def back_to_admin_menu(callback: CallbackQuery, is_main_admin: bool) -> None:
    if not is_main_admin:
        return
    await callback.message.edit_text(
        "👑 **مدیریت ادمین‌ها**\n\nاز منوی زیر عمل مورد نظر را انتخاب کنید:",
        reply_markup=_admin_management_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()
