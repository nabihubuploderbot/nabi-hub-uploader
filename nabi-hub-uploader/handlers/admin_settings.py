"""
handlers/admin_settings.py — Admin settings command handlers.

Handles /set* commands for configuring bot settings.
"""

from __future__ import annotations

from typing import Callable

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings
from services.setting_service import SettingService, SettingKeys
from services.admin_service import AdminService
from services.channel_service import ChannelService
from keyboards.reply import admin_reply_menu, remove_keyboard
from keyboards.inline import admin_settings_menu

router = Router(name="admin_settings")


# ── FSM States for Settings ─────────────────────────


class SettingStates(StatesGroup):
    """FSM states for various settings."""
    waiting_welcome = State()
    waiting_force_msg = State()
    waiting_reaction_msg = State()
    waiting_caption = State()
    waiting_delay = State()
    waiting_password = State()
    waiting_button = State()
    waiting_channel_id = State()
    waiting_channel_username = State()
    waiting_reaction_channel = State()
    waiting_reaction_message = State()
    waiting_admin_id = State()
    waiting_remove_admin_id = State()
    waiting_remove_channel_id = State()
    forward_broadcast = State()
    waiting_file_token = State()


# ═══════════════════════════════════════════════════════
# SET WELCOME MESSAGE
# ═══════════════════════════════════════════════════════


@router.message(F.text == "/setwelcome")
async def start_set_welcome(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Start setting welcome message."""
    if not is_admin:
        return

    await state.set_state(SettingStates.waiting_welcome)
    await message.answer(
        "📝 لطفاً پیام خوش‌آمدگویی جدید را ارسال کنید:\n\n"
        "از Markdown می‌توانید استفاده کنید.",
        reply_markup=remove_keyboard(),
    )


@router.message(SettingStates.waiting_welcome)
async def set_welcome(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Set the welcome message."""
    await SettingService.set(session, SettingKeys.WELCOME_MESSAGE, message.text or message.caption)
    await state.clear()
    await message.answer("✅ پیام خوش‌آمدگویی تنظیم شد.", reply_markup=admin_reply_menu())


# ═══════════════════════════════════════════════════════
# SET FORCE JOIN MESSAGE
# ═══════════════════════════════════════════════════════


@router.message(F.text == "/setforcemsg")
async def start_set_force_msg(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Start setting force join message."""
    if not is_admin:
        return

    await state.set_state(SettingStates.waiting_force_msg)
    await message.answer(
        "🔒 لطفاً پیام قفل عضویت اجباری جدید را ارسال کنید:",
        reply_markup=remove_keyboard(),
    )


@router.message(SettingStates.waiting_force_msg)
async def set_force_msg(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Set the force join message."""
    await SettingService.set(session, SettingKeys.FORCE_JOIN_MESSAGE, message.text)
    await state.clear()
    await message.answer("✅ پیام قفل عضویت تنظیم شد.", reply_markup=admin_reply_menu())


# ═══════════════════════════════════════════════════════
# SET REACTION LOCK MESSAGE
# ═══════════════════════════════════════════════════════


@router.message(F.text == "/setreactionmsg")
async def start_set_reaction_msg(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Start setting reaction lock message."""
    if not is_admin:
        return

    await state.set_state(SettingStates.waiting_reaction_msg)
    await message.answer(
        "❤️ لطفاً پیام قفل واکنش جدید را ارسال کنید:",
        reply_markup=remove_keyboard(),
    )


@router.message(SettingStates.waiting_reaction_msg)
async def set_reaction_msg(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Set the reaction lock message."""
    await SettingService.set(session, SettingKeys.REACTION_LOCK_MESSAGE, message.text)
    await state.clear()
    await message.answer("✅ پیام قفل واکنش تنظیم شد.", reply_markup=admin_reply_menu())


# ═══════════════════════════════════════════════════════
# SET DELAY TIMER
# ═══════════════════════════════════════════════════════


@router.message(F.text == "/setdelay")
async def cmd_set_delay(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Start setting delay timer."""
    if not is_admin:
        return

    args = message.text.split()
    if len(args) >= 2:
        try:
            seconds = int(args[1])
            await SettingService.set(session, SettingKeys.DELAY_BEFORE_SEND, str(seconds), "int")
            await message.answer(f"✅ تایمر تنظیم شد: {seconds} ثانیه.")
            return
        except ValueError:
            pass

    await state.set_state(SettingStates.waiting_delay)
    await message.answer(
        "⏱ لطفاً تأخیر مورد نظر (به ثانیه) را وارد کنید:",
        reply_markup=remove_keyboard(),
    )


@router.message(SettingStates.waiting_delay)
async def set_delay(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Set the delay timer."""
    try:
        seconds = int(message.text.strip())
        if seconds < 0 or seconds > 300:
            await message.answer("⚠️ مقدار باید بین 0 تا 300 باشد.")
            return
        await SettingService.set(session, SettingKeys.DELAY_BEFORE_SEND, str(seconds), "int")
        await state.clear()
        await message.answer(
            f"✅ تایمر تنظیم شد: {seconds} ثانیه.",
            reply_markup=admin_reply_menu(),
        )
    except ValueError:
        await message.answer("⚠️ لطفاً یک عدد صحیح وارد کنید.")


# ═══════════════════════════════════════════════════════
# SET PASSWORD
# ═══════════════════════════════════════════════════════


@router.message(F.text == "/setpassword")
async def cmd_set_password(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_main_admin: bool,
) -> None:
    """Start setting access password."""
    if not is_main_admin:
        return

    args = message.text.split()
    if len(args) >= 2:
        password = " ".join(args[1:])
        await SettingService.set(session, SettingKeys.PASSWORD, password)
        await message.answer("✅ پسورد تنظیم شد.")
        return

    await state.set_state(SettingStates.waiting_password)
    await message.answer(
        "🔑 لطفاً پسورد جدید را وارد کنید:",
        reply_markup=remove_keyboard(),
    )


@router.message(SettingStates.waiting_password)
async def set_password(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Set the access password."""
    password = message.text.strip()
    await SettingService.set(session, SettingKeys.PASSWORD, password)
    await state.clear()
    await message.answer("✅ پسورد تنظیم شد.", reply_markup=admin_reply_menu())


@router.message(F.text == "/clearpassword")
async def clear_password(
    message: Message,
    session: AsyncSession,
    is_main_admin: bool,
) -> None:
    """Clear the access password."""
    if not is_main_admin:
        return
    await SettingService.delete(session, SettingKeys.PASSWORD)
    await message.answer("🔓 پسورد حذف شد.")


# ═══════════════════════════════════════════════════════
# SET BUTTON
# ═══════════════════════════════════════════════════════


@router.message(F.text.startswith("/setbtn"))
async def cmd_set_button(
    message: Message,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Set inline button text and URL. Usage: /setbtn <text> <url>"""
    if not is_admin:
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ استفاده: /setbtn <متن دکمه> <لینک>")
        return

    btn_text = args[1]
    btn_url = args[2]

    if not btn_url.startswith(("http://", "https://")):
        await message.answer("⚠️ لینک باید با http:// یا https:// شروع شود.")
        return

    await SettingService.set(session, SettingKeys.BUTTON_TEXT, btn_text)
    await SettingService.set(session, SettingKeys.BUTTON_URL, btn_url)
    await message.answer(f"✅ دکمه تنظیم شد:\n📝 متن: {btn_text}\n🔗 لینک: {btn_url}")


@router.message(F.text == "/togglebtn")
async def toggle_buttons(
    message: Message,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Toggle button visibility."""
    if not is_admin:
        return

    current = await SettingService.get_bool(session, SettingKeys.SHOW_BUTTONS, default=True)
    new_val = not current
    await SettingService.set(session, SettingKeys.SHOW_BUTTONS, str(new_val).lower(), "bool")
    status = "فعال" if new_val else "غیرفعال"
    await message.answer(f"🔘 نمایش دکمه‌ها: {status}")


# ═══════════════════════════════════════════════════════
# ADD FORCE JOIN CHANNEL
# ═══════════════════════════════════════════════════════


@router.message(F.text == "/addchannel" or F.text.startswith("/addchannel "))
async def cmd_add_channel(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Start adding a force-join channel."""
    if not is_admin:
        return

    args = message.text.split()
    if len(args) >= 2:
        # Direct add with channel ID
        try:
            channel_id = int(args[1])
            username = args[2] if len(args) >= 3 else None

            await ChannelService.add_channel(
                session=session,
                channel_id=channel_id,
                channel_username=username,
            )
            await message.answer(f"✅ کانال {channel_id} اضافه شد.")
            return
        except (ValueError, IndexError):
            pass

    await state.set_state(SettingStates.waiting_channel_id)
    await message.answer(
        "📢 لطفاً آیدی کانال را وارد کنید:\n\n"
        "مثال: -1001234567890\n\n"
        "برای کانال‌های عمومی می‌توانید نام کاربری (@channel) را هم وارد کنید.",
        reply_markup=remove_keyboard(),
    )


@router.message(SettingStates.waiting_channel_id)
async def process_channel_id(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot,
    t: Callable[[str], str],
) -> None:
    """Process channel ID input."""
    text = message.text.strip()

    channel_id = None
    channel_username = None

    # Try parsing as numeric ID
    try:
        channel_id = int(text)
    except ValueError:
        # Try as username
        if text.startswith("@"):
            channel_username = text[1:]
        elif text.startswith("https://t.me/"):
            channel_username = text.split("/")[-1]
        else:
            channel_username = text

    # If we have username, try to resolve the ID
    if channel_username and not channel_id:
        from utils.telegram import get_chat_info
        chat_info = await get_chat_info(bot, channel_username)
        if chat_info:
            channel_id = chat_info["id"]
        else:
            await message.answer("⚠️ کانال یافت نشد. لطفاً آیدی عددی را وارد کنید.")
            return

    if not channel_id:
        await message.answer("⚠️ آیدی نامعتبر است.")
        return

    # Get channel info for display
    from utils.telegram import get_chat_info
    chat_info = await get_chat_info(bot, channel_id)

    await ChannelService.add_channel(
        session=session,
        channel_id=channel_id,
        channel_username=channel_username,
        channel_title=chat_info.get("title") if chat_info else None,
        invite_link=chat_info.get("invite_link") if chat_info else None,
    )

    await state.clear()
    title = chat_info.get("title", str(channel_id)) if chat_info else str(channel_id)
    await message.answer(
        f"✅ کانال اضافه شد:\n📢 {title}\n🆔 {channel_id}",
        reply_markup=admin_reply_menu(),
    )


# ═══════════════════════════════════════════════════════
# REMOVE FORCE JOIN CHANNEL
# ═══════════════════════════════════════════════════════


@router.message(F.text == "/removechannel" or F.text.startswith("/removechannel "))
async def cmd_remove_channel(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Remove a force-join channel."""
    if not is_admin:
        return

    args = message.text.split()
    if len(args) >= 2:
        try:
            channel_id = int(args[1])
            removed = await ChannelService.remove_channel(session, channel_id)
            if removed:
                await message.answer(f"✅ کانال {channel_id} حذف شد.")
            else:
                await message.answer("⚠️ کانال یافت نشد.")
            return
        except ValueError:
            pass

    # Show list and ask
    channels = await ChannelService.get_all_channels(session)
    if not channels:
        await message.answer("⚠️ هیچ کانالی تنظیم نشده است.")
        return

    text = "📋 **کانال‌های فعلی:**\n\n"
    for ch in channels:
        status = "✅" if ch.is_active else "❌"
        text += f"{status} {ch.display_name} (🆔 {ch.channel_id})\n"

    text += "\nبرای حذف: /removechannel <آیدی>"
    await message.answer(text, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════
# LIST CHANNELS
# ═══════════════════════════════════════════════════════


@router.message(F.text == "/channels")
async def cmd_list_channels(
    message: Message,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """List all force-join channels."""
    if not is_admin:
        return

    channels = await ChannelService.get_all_channels(session)
    if not channels:
        await message.answer("⚠️ هیچ کانال قفل‌شده‌ای وجود ندارد.")
        return

    text = "📋 **کانال‌های قفل عضویت:**\n\n"
    for i, ch in enumerate(channels, 1):
        status = "✅ فعال" if ch.is_active else "❌ غیرفعال"
        text += (
            f"{i}. {ch.display_name}\n"
            f"   🆔 `{ch.channel_id}`\n"
            f"   📊 {status}\n"
            f"   🔗 {ch.join_link}\n\n"
        )

    await message.answer(text, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════
# ADD REACTION LOCK
# ═══════════════════════════════════════════════════════


@router.message(F.text == "/addreaction")
async def cmd_add_reaction(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Start adding a reaction lock."""
    if not is_admin:
        return

    await state.set_state(SettingStates.waiting_reaction_channel)
    await message.answer(
        "❤️ لطفاً آیدی کانال حاوی پست مورد نظر را وارد کنید:\n\n"
        "مثال: -1001234567890",
        reply_markup=remove_keyboard(),
    )


@router.message(SettingStates.waiting_reaction_channel)
async def process_reaction_channel(
    message: Message,
    state: FSMContext,
) -> None:
    """Process reaction lock channel ID."""
    try:
        channel_id = int(message.text.strip())
        await state.update_data(reaction_channel_id=channel_id)
        await state.set_state(SettingStates.waiting_reaction_message)
        await message.answer("💬 لطفاً آیدی پیام مورد نظر را وارد کنید:")
    except ValueError:
        await message.answer("⚠️ آیدی نامعتبر. لطفاً یک عدد صحیح وارد کنید.")


@router.message(SettingStates.waiting_reaction_message)
async def process_reaction_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Process reaction lock message ID and save."""
    try:
        message_id = int(message.text.strip())
        data = await state.get_data()
        channel_id = data.get("reaction_channel_id")

        await ChannelService.add_reaction_lock(
            session=session,
            channel_id=channel_id,
            message_id=message_id,
        )

        await state.clear()
        await message.answer(
            f"✅ قفل واکنش اضافه شد:\n"
            f"📢 کانال: `{channel_id}`\n"
            f"💬 پیام: `{message_id}`",
            parse_mode="Markdown",
            reply_markup=admin_reply_menu(),
        )
    except ValueError:
        await message.answer("⚠️ آیدی نامعتبر.")


# ═══════════════════════════════════════════════════════
# ADD/REMOVE ADMIN
# ═══════════════════════════════════════════════════════


@router.message(F.text == "/addadmin" or F.text.startswith("/addadmin "))
async def cmd_add_admin(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_main_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Add a new admin."""
    if not is_main_admin:
        await message.answer("⛔ فقط ادمین اصلی می‌تواند ادمین اضافه کند.")
        return

    args = message.text.split()
    if len(args) >= 2:
        try:
            user_id = int(args[1])
            admin = await AdminService.add_admin(session, user_id)
            await message.answer(f"✅ ادمین جدید اضافه شد: {user_id}")
            return
        except ValueError:
            pass

    await state.set_state(SettingStates.waiting_admin_id)
    await message.answer(
        "👑 لطفاً آیدی عددی کاربر مورد نظر برای ادمین شدن را وارد کنید:",
        reply_markup=remove_keyboard(),
    )


@router.message(SettingStates.waiting_admin_id)
async def process_admin_id(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Process admin ID input."""
    try:
        user_id = int(message.text.strip())
        admin = await AdminService.add_admin(session, user_id)
        await state.clear()
        await message.answer(
            f"✅ ادمین جدید اضافه شد: {user_id}",
            reply_markup=admin_reply_menu(),
        )
    except ValueError:
        await message.answer("⚠️ آیدی نامعتبر.")


@router.message(F.text == "/removeadmin" or F.text.startswith("/removeadmin "))
async def cmd_remove_admin(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_main_admin: bool,
    t: Callable[[str], str],
) -> None:
    """Remove an admin."""
    if not is_main_admin:
        await message.answer("⛔ فقط ادمین اصلی می‌تواند ادمین حذف کند.")
        return

    args = message.text.split()
    if len(args) >= 2:
        try:
            user_id = int(args[1])
            removed = await AdminService.remove_admin(session, user_id)
            if removed:
                await message.answer(f"✅ ادمین حذف شد: {user_id}")
            else:
                await message.answer("⚠️ ادمین یافت نشد یا ادمین اصلی است.")
            return
        except ValueError:
            pass

    # Show list
    admins = await AdminService.get_all_admins(session)
    text = "👑 **لیست ادمین‌ها:**\n\n"
    for admin in admins:
        role = "⭐ اصلی" if admin.is_main_admin else "👤"
        text += f"{role} `{admin.user_id}` - {admin.full_name or 'N/A'}\n"
    text += "\nبرای حذف: /removeadmin <آیدی>"
    await message.answer(text, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════
# CAPTION COMMANDS
# ═══════════════════════════════════════════════════════


@router.message(F.text.startswith("/setcaption"))
async def cmd_set_caption(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Set file caption. Usage: /setcaption <text>"""
    if not is_admin:
        return

    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        caption = args[1]
        await SettingService.set(session, SettingKeys.FILE_CAPTION, caption)
        await message.answer(f"✅ کپشن تنظیم شد:\n{caption}")
        return

    await state.set_state(SettingStates.waiting_caption)
    await message.answer(
        "📝 لطفاً کپشن مورد نظر را ارسال کنید:",
        reply_markup=remove_keyboard(),
    )


@router.message(SettingStates.waiting_caption)
async def set_caption(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    t: Callable[[str], str],
) -> None:
    """Set caption from FSM state."""
    caption = message.text or ""
    await SettingService.set(session, SettingKeys.FILE_CAPTION, caption)
    await state.clear()
    await message.answer("✅ کپشن تنظیم شد.", reply_markup=admin_reply_menu())


@router.message(F.text == "/clearcaption")
async def clear_caption(
    message: Message,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Clear file caption."""
    if not is_admin:
        return
    await SettingService.delete(session, SettingKeys.FILE_CAPTION)
    await message.answer("🗑 کپشن حذف شد.")


# ═══════════════════════════════════════════════════════
# ADMIN LIST
# ═══════════════════════════════════════════════════════


@router.message(F.text == "/admins")
async def cmd_list_admins(
    message: Message,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """List all admins."""
    if not is_admin:
        return

    admins = await AdminService.get_all_admins(session)
    text = "👑 **لیست ادمین‌ها:**\n\n"
    for i, admin in enumerate(admins, 1):
        role = "⭐ اصلی" if admin.is_main_admin else "👤"
        perms = []
        if admin.can_upload:
            perms.append("📤")
        if admin.can_broadcast:
            perms.append("📢")
        if admin.can_manage_users:
            perms.append("👥")
        if admin.can_manage_settings:
            perms.append("⚙️")
        text += f"{i}. {role} `{admin.user_id}`\n   {''.join(perms)}\n"
    await message.answer(text, parse_mode="Markdown")
