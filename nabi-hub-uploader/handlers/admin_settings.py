"""
admin_settings.py — هندلرهای تنظیمات ادمین

✅ همه دستورات با Command() filter — منوی همبرگری کار میکنه
✅ همه پیام‌ها دکمه اینلاین دارن
"""

from __future__ import annotations

from typing import Callable

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings
from services.setting_service import SettingService, SettingKeys
from services.admin_service import AdminService
from services.channel_service import ChannelService
from keyboards.reply import admin_reply_menu, remove_keyboard
from keyboards.inline import (
    CD,
    panel_button,
    settings_button,
    cancel_panel_button,
)

router = Router(name="admin_settings")


class SettingStates(StatesGroup):
    waiting_welcome = State()
    waiting_force_msg = State()
    waiting_reaction_msg = State()
    waiting_caption = State()
    waiting_delay = State()
    waiting_password = State()
    waiting_channel_id = State()


# ✅ تابع کمکی: گرفتن آرگومان‌ها از دستور
def _get_args(command: CommandObject) -> str:
    """گرفتن آرگومان بعد از دستور."""
    return command.args or ""


# ═══════════════════════════════════════════════════════
# /setwelcome
# ═══════════════════════════════════════════════════════


@router.message(Command("setwelcome"))
async def cmd_set_welcome(message: Message, state: FSMContext, session: AsyncSession, is_admin: bool, command: CommandObject) -> None:
    if not is_admin:
        return
    args = _get_args(command)
    if args:
        await SettingService.set(session, SettingKeys.WELCOME_MESSAGE, args)
        await message.answer("✅ **پیام خوش‌آمدگویی تنظیم شد.**", parse_mode="Markdown", reply_markup=settings_button())
        return
    await state.set_state(SettingStates.waiting_welcome)
    await message.answer(
        "📝 **تنظیم پیام خوش‌آمدگویی**\n\nپیام جدید را ارسال کنید:",
        parse_mode="Markdown", reply_markup=cancel_panel_button(),
    )


@router.message(SettingStates.waiting_welcome)
async def set_welcome(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await SettingService.set(session, SettingKeys.WELCOME_MESSAGE, message.text or message.caption)
    await state.clear()
    await message.answer("✅ **پیام خوش‌آمدگویی تنظیم شد.**", parse_mode="Markdown", reply_markup=panel_button())


# ═══════════════════════════════════════════════════════
# /setforcemsg
# ═══════════════════════════════════════════════════════


@router.message(Command("setforcemsg"))
async def cmd_set_force_msg(message: Message, state: FSMContext, session: AsyncSession, is_admin: bool, command: CommandObject) -> None:
    if not is_admin:
        return
    args = _get_args(command)
    if args:
        await SettingService.set(session, SettingKeys.FORCE_JOIN_MESSAGE, args)
        await message.answer("✅ **پیام قفل عضویت تنظیم شد.**", parse_mode="Markdown", reply_markup=settings_button())
        return
    await state.set_state(SettingStates.waiting_force_msg)
    await message.answer("🔒 **تنظیم پیام قفل عضویت**\n\nپیام جدید را ارسال کنید:", parse_mode="Markdown", reply_markup=cancel_panel_button())


@router.message(SettingStates.waiting_force_msg)
async def set_force_msg(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await SettingService.set(session, SettingKeys.FORCE_JOIN_MESSAGE, message.text)
    await state.clear()
    await message.answer("✅ **پیام قفل عضویت تنظیم شد.**", parse_mode="Markdown", reply_markup=panel_button())


# ═══════════════════════════════════════════════════════
# /setreactionmsg
# ═══════════════════════════════════════════════════════


@router.message(Command("setreactionmsg"))
async def cmd_set_reaction_msg(message: Message, state: FSMContext, session: AsyncSession, is_admin: bool, command: CommandObject) -> None:
    if not is_admin:
        return
    args = _get_args(command)
    if args:
        await SettingService.set(session, SettingKeys.REACTION_LOCK_MESSAGE, args)
        await message.answer("✅ **پیام قفل واکنش تنظیم شد.**", parse_mode="Markdown", reply_markup=settings_button())
        return
    await state.set_state(SettingStates.waiting_reaction_msg)
    await message.answer("❤️ **تنظیم پیام قفل واکنش**\n\nپیام جدید را ارسال کنید:", parse_mode="Markdown", reply_markup=cancel_panel_button())


@router.message(SettingStates.waiting_reaction_msg)
async def set_reaction_msg(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await SettingService.set(session, SettingKeys.REACTION_LOCK_MESSAGE, message.text)
    await state.clear()
    await message.answer("✅ **پیام قفل واکنش تنظیم شد.**", parse_mode="Markdown", reply_markup=panel_button())


# ═══════════════════════════════════════════════════════
# /setdelay
# ═══════════════════════════════════════════════════════


@router.message(Command("setdelay"))
async def cmd_set_delay(message: Message, state: FSMContext, session: AsyncSession, is_admin: bool, command: CommandObject) -> None:
    if not is_admin:
        return
    args = _get_args(command)
    if args:
        try:
            seconds = int(args)
            await SettingService.set(session, SettingKeys.DELAY_BEFORE_SEND, str(seconds), "int")
            await message.answer(f"✅ **تایمر تنظیم شد:** {seconds} ثانیه", parse_mode="Markdown", reply_markup=settings_button())
            return
        except ValueError:
            pass
    await state.set_state(SettingStates.waiting_delay)
    await message.answer("⏱ **تنظیم تایمر**\n\nعدد (به ثانیه) را وارد کنید:", parse_mode="Markdown", reply_markup=cancel_panel_button())


@router.message(SettingStates.waiting_delay)
async def set_delay(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        seconds = int(message.text.strip())
        if seconds < 0 or seconds > 300:
            await message.answer("⚠️ مقدار باید بین ۰ تا ۳۰۰ باشد.", reply_markup=cancel_panel_button())
            return
        await SettingService.set(session, SettingKeys.DELAY_BEFORE_SEND, str(seconds), "int")
        await state.clear()
        await message.answer(f"✅ **تایمر تنظیم شد:** {seconds} ثانیه", parse_mode="Markdown", reply_markup=settings_button())
    except ValueError:
        await message.answer("⚠️ لطفاً یک عدد صحیح وارد کنید.", reply_markup=cancel_panel_button())


# ═══════════════════════════════════════════════════════
# /setpassword
# ═══════════════════════════════════════════════════════


@router.message(Command("setpassword"))
async def cmd_set_password(message: Message, state: FSMContext, session: AsyncSession, is_main_admin: bool, command: CommandObject) -> None:
    if not is_main_admin:
        return
    args = _get_args(command)
    if args:
        await SettingService.set(session, SettingKeys.PASSWORD, args)
        await message.answer("✅ **پسورد تنظیم شد.**", parse_mode="Markdown", reply_markup=settings_button())
        return
    await state.set_state(SettingStates.waiting_password)
    await message.answer("🔑 **تنظیم پسورد**\n\nپسورد جدید را وارد کنید:", parse_mode="Markdown", reply_markup=cancel_panel_button())


@router.message(SettingStates.waiting_password)
async def set_password(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await SettingService.set(session, SettingKeys.PASSWORD, message.text.strip())
    await state.clear()
    await message.answer("✅ **پسورد تنظیم شد.**", parse_mode="Markdown", reply_markup=settings_button())


@router.message(Command("clearpassword"))
async def cmd_clear_password(message: Message, session: AsyncSession, is_main_admin: bool) -> None:
    if not is_main_admin:
        return
    await SettingService.delete(session, SettingKeys.PASSWORD)
    await message.answer("🔓 **پسورد حذف شد.**", parse_mode="Markdown", reply_markup=settings_button())


# ═══════════════════════════════════════════════════════
# /setbtn
# ═══════════════════════════════════════════════════════


@router.message(Command("setbtn"))
async def cmd_set_button(message: Message, session: AsyncSession, is_admin: bool, command: CommandObject) -> None:
    if not is_admin:
        return
    args_text = _get_args(command)
    parts = args_text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ **استفاده:** `/setbtn متن_دکمه لینک`", parse_mode="Markdown", reply_markup=settings_button())
        return
    btn_text, btn_url = parts[0], parts[1]
    if not btn_url.startswith(("http://", "https://")):
        await message.answer("⚠️ لینک باید با http:// شروع شود.", reply_markup=settings_button())
        return
    await SettingService.set(session, SettingKeys.BUTTON_TEXT, btn_text)
    await SettingService.set(session, SettingKeys.BUTTON_URL, btn_url)
    await message.answer(f"✅ **دکمه تنظیم شد:**\n📝 {btn_text}\n🔗 {btn_url}", parse_mode="Markdown", reply_markup=settings_button())


@router.message(Command("togglebtn"))
async def cmd_toggle_buttons(message: Message, session: AsyncSession, is_admin: bool) -> None:
    if not is_admin:
        return
    current = await SettingService.get_bool(session, SettingKeys.SHOW_BUTTONS, default=True)
    new_val = not current
    await SettingService.set(session, SettingKeys.SHOW_BUTTONS, str(new_val).lower(), "bool")
    status = "✅ فعال" if new_val else "❌ غیرفعال"
    await message.answer(f"🔘 **نمایش دکمه‌ها:** {status}", parse_mode="Markdown", reply_markup=settings_button())


# ═══════════════════════════════════════════════════════
# /addchannel
# ═══════════════════════════════════════════════════════


@router.message(Command("addchannel"))
async def cmd_add_channel(message: Message, state: FSMContext, session: AsyncSession, is_admin: bool, command: CommandObject) -> None:
    if not is_admin:
        return
    args_text = _get_args(command)
    if args_text:
        parts = args_text.split()
        try:
            channel_id = int(parts[0])
            username = parts[1] if len(parts) >= 2 else None
            await ChannelService.add_channel(session=session, channel_id=channel_id, channel_username=username)
            await message.answer(f"✅ **کانال اضافه شد:** `{channel_id}`", parse_mode="Markdown", reply_markup=settings_button())
            return
        except (ValueError, IndexError):
            pass
    await state.set_state(SettingStates.waiting_channel_id)
    await message.answer(
        "📢 **افزودن کانال قفل عضویت**\n\nآیدی عددی کانال را وارد کنید:\n\nمثال: `-1001234567890`",
        parse_mode="Markdown", reply_markup=cancel_panel_button(),
    )


@router.message(SettingStates.waiting_channel_id)
async def process_channel_id(message: Message, state: FSMContext, session: AsyncSession, bot) -> None:
    text = message.text.strip()
    channel_id = None
    channel_username = None
    try:
        channel_id = int(text)
    except ValueError:
        if text.startswith("@"):
            channel_username = text[1:]
        elif text.startswith("https://t.me/"):
            channel_username = text.split("/")[-1]
        else:
            channel_username = text
    if channel_username and not channel_id:
        from utils.telegram import get_chat_info
        chat_info = await get_chat_info(bot, channel_username)
        if chat_info:
            channel_id = chat_info["id"]
        else:
            await message.answer("⚠️ **کانال یافت نشد!**\n\nآیدی عددی را وارد کنید.", parse_mode="Markdown", reply_markup=cancel_panel_button())
            return
    if not channel_id:
        await message.answer("⚠️ آیدی نامعتبر است.", reply_markup=cancel_panel_button())
        return
    from utils.telegram import get_chat_info
    chat_info = await get_chat_info(bot, channel_id)
    await ChannelService.add_channel(
        session=session, channel_id=channel_id, channel_username=channel_username,
        channel_title=chat_info.get("title") if chat_info else None,
        invite_link=chat_info.get("invite_link") if chat_info else None,
    )
    await state.clear()
    title = chat_info.get("title", str(channel_id)) if chat_info else str(channel_id)
    await message.answer(f"✅ **کانال اضافه شد!**\n\n📢 {title}\n🆔 `{channel_id}`", parse_mode="Markdown", reply_markup=settings_button())


# ═══════════════════════════════════════════════════════
# /removechannel
# ═══════════════════════════════════════════════════════


@router.message(Command("removechannel"))
async def cmd_remove_channel(message: Message, session: AsyncSession, is_admin: bool, command: CommandObject) -> None:
    if not is_admin:
        return
    args_text = _get_args(command)
    if args_text:
        try:
            channel_id = int(args_text.split()[0])
            removed = await ChannelService.remove_channel(session, channel_id)
            if removed:
                await message.answer(f"✅ **کانال حذف شد:** `{channel_id}`", parse_mode="Markdown", reply_markup=settings_button())
            else:
                await message.answer("⚠️ کانال یافت نشد.", reply_markup=settings_button())
            return
        except ValueError:
            pass
    channels = await ChannelService.get_all_channels(session)
    if not channels:
        await message.answer("⚠️ هیچ کانالی تنظیم نشده.", reply_markup=settings_button())
        return
    text = "📋 **کانال‌های فعلی:**\n\n"
    for ch in channels:
        s = "✅" if ch.is_active else "❌"
        text += f"{s} {ch.display_name} (🆔 `{ch.channel_id}`)\n"
    text += "\nبرای حذف: `/removechannel <آیدی>`"
    await message.answer(text, parse_mode="Markdown", reply_markup=settings_button())


# ═══════════════════════════════════════════════════════
# /channels
# ═══════════════════════════════════════════════════════


@router.message(Command("channels"))
async def cmd_list_channels(message: Message, session: AsyncSession, is_admin: bool) -> None:
    if not is_admin:
        return
    channels = await ChannelService.get_all_channels(session)
    if not channels:
        await message.answer("⚠️ هیچ کانال قفل‌شده‌ای وجود ندارد.", reply_markup=settings_button())
        return
    text = "📋 **کانال‌های قفل عضویت:**\n\n"
    for i, ch in enumerate(channels, 1):
        s = "✅ فعال" if ch.is_active else "❌ غیرفعال"
        text += f"{i}. {ch.display_name}\n   🆔 `{ch.channel_id}`\n   📊 {s}\n   🔗 {ch.join_link}\n\n"
    await message.answer(text, parse_mode="Markdown", reply_markup=settings_button())


# ═══════════════════════════════════════════════════════
# /addreaction
# ═══════════════════════════════════════════════════════


@router.message(Command("addreaction"))
async def cmd_add_reaction(message: Message, state: FSMContext, session: AsyncSession, is_admin: bool) -> None:
    if not is_admin:
        return
    await state.set_state(SettingStates.waiting_channel_id)
    await message.answer(
        "❤️ **افزودن قفل واکنش**\n\nآیدی کانال حاوی پست را وارد کنید:\n\nمثال: `-1001234567890`",
        parse_mode="Markdown", reply_markup=cancel_panel_button(),
    )


# ═══════════════════════════════════════════════════════
# /setcaption
# ═══════════════════════════════════════════════════════


@router.message(Command("setcaption"))
async def cmd_set_caption(message: Message, state: FSMContext, session: AsyncSession, is_admin: bool, command: CommandObject) -> None:
    if not is_admin:
        return
    args = _get_args(command)
    if args:
        await SettingService.set(session, SettingKeys.FILE_CAPTION, args)
        await message.answer(f"✅ **کپشن تنظیم شد:**\n\n{args}", parse_mode="Markdown", reply_markup=settings_button())
        return
    await state.set_state(SettingStates.waiting_caption)
    await message.answer("📝 **تنظیم کپشن**\n\nکپشن مورد نظر را ارسال کنید:", parse_mode="Markdown", reply_markup=cancel_panel_button())


@router.message(SettingStates.waiting_caption)
async def set_caption(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await SettingService.set(session, SettingKeys.FILE_CAPTION, message.text or "")
    await state.clear()
    await message.answer("✅ **کپشن تنظیم شد.**", parse_mode="Markdown", reply_markup=settings_button())


@router.message(Command("clearcaption"))
async def cmd_clear_caption(message: Message, session: AsyncSession, is_admin: bool) -> None:
    if not is_admin:
        return
    await SettingService.delete(session, SettingKeys.FILE_CAPTION)
    await message.answer("🗑 **کپشن حذف شد.**", parse_mode="Markdown", reply_markup=settings_button())


# ═══════════════════════════════════════════════════════
# /admins
# ═══════════════════════════════════════════════════════


@router.message(Command("admins"))
async def cmd_list_admins(message: Message, session: AsyncSession, is_admin: bool) -> None:
    if not is_admin:
        return
    admins = await AdminService.get_all_admins(session)
    text = "👑 **لیست ادمین‌ها:**\n\n"
    for i, admin in enumerate(admins, 1):
        role = "⭐ اصلی" if admin.is_main_admin else "👤"
        perms = []
        if admin.can_upload: perms.append("📤")
        if admin.can_broadcast: perms.append("📢")
        if admin.can_manage_users: perms.append("👥")
        if admin.can_manage_settings: perms.append("⚙️")
        text += f"{i}. {role} `{admin.user_id}`\n   {''.join(perms)}\n"
    await message.answer(text, parse_mode="Markdown", reply_markup=settings_button())


# ═══════════════════════════════════════════════════════
# /addadmin
# ═══════════════════════════════════════════════════════


@router.message(Command("addadmin"))
async def cmd_add_admin(message: Message, state: FSMContext, session: AsyncSession, is_main_admin: bool, command: CommandObject) -> None:
    if not is_main_admin:
        await message.answer("⛔ فقط ادمین اصلی.", reply_markup=panel_button())
        return
    args = _get_args(command)
    if args:
        try:
            user_id = int(args.split()[0])
            await AdminService.add_admin(session, user_id)
            await message.answer(f"✅ **ادمین اضافه شد:** `{user_id}`", parse_mode="Markdown", reply_markup=settings_button())
            return
        except ValueError:
            pass
    await state.set_state(SettingStates.waiting_channel_id)
    await message.answer("👑 **افزودن ادمین**\n\nآیدی عددی کاربر:", parse_mode="Markdown", reply_markup=cancel_panel_button())


# ═══════════════════════════════════════════════════════
# /removeadmin
# ═══════════════════════════════════════════════════════


@router.message(Command("removeadmin"))
async def cmd_remove_admin(message: Message, session: AsyncSession, is_main_admin: bool, command: CommandObject) -> None:
    if not is_main_admin:
        await message.answer("⛔ فقط ادمین اصلی.", reply_markup=panel_button())
        return
    args = _get_args(command)
    if args:
        try:
            user_id = int(args.split()[0])
            removed = await AdminService.remove_admin(session, user_id)
            if removed:
                await message.answer(f"✅ **ادمین حذف شد:** `{user_id}`", parse_mode="Markdown", reply_markup=settings_button())
            else:
                await message.answer("⚠️ ادمین یافت نشد.", reply_markup=settings_button())
            return
        except ValueError:
            pass
    admins = await AdminService.get_all_admins(session)
    text = "👑 **لیست ادمین‌ها:**\n\n"
    for admin in admins:
        role = "⭐ اصلی" if admin.is_main_admin else "👤"
        text += f"{role} `{admin.user_id}` - {admin.full_name or 'N/A'}\n"
    text += "\nبرای حذف: `/removeadmin <آیدی>`"
    await message.answer(text, parse_mode="Markdown", reply_markup=settings_button())
