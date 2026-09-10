"""
admin_locks.py — مدیریت قفل عضویت و قفل واکنش

همه دکمه‌ها کار می‌کنن ✅
"""

from __future__ import annotations

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from services.channel_service import ChannelService
from keyboards.inline import (
    CD,
    panel_button,
    settings_button,
    cancel_panel_button,
    force_join_menu,
    reaction_lock_menu,
    back_button,
)

router = Router(name="admin_locks")


# ── FSM States ──────────────────────────────────────

class LockStates(StatesGroup):
    waiting_fj_channel_id = State()       # افزودن کانال قفل عضویت
    waiting_rl_channel_id = State()       # افزودن کانال قفل واکنش
    waiting_rl_message_id = State()       # افزودن پیام قفل واکنش


# ═══════════════════════════════════════════════════════
# 🔒 قفل عضویت اجباری (Force Join)
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.SETTINGS_FORCE_JOIN)
async def show_force_join(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    """نمایش منوی قفل عضویت."""
    if not is_admin:
        return

    channels = await ChannelService.get_active_channels(session)
    text = "🔒 **قفل عضویت اجباری**\n\n"
    if channels:
        for ch in channels:
            text += f"✅ {ch.display_name} (`{ch.channel_id}`)\n"
    else:
        text += "⚠️ هیچ کانال فعالی وجود ندارد.\n"
    text += "\nاز منوی زیر عمل مورد نظر را انتخاب کنید:"

    await callback.message.edit_text(
        text,
        reply_markup=force_join_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ── ➕ افزودن کانال ────────────────────────────────


@router.callback_query(F.data == CD.FJ_ADD)
async def fj_add_start(callback: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    """شروع افزودن کانال به قفل عضویت."""
    if not is_admin:
        return

    await state.set_state(LockStates.waiting_fj_channel_id)
    await callback.message.edit_text(
        "➕ **افزودن کانال به قفل عضویت**\n\n"
        "آیدی عددی کانال را وارد کنید:\n\n"
        "مثال: `-1001234567890`\n"
        "یا: `@channel_username`",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(LockStates.waiting_fj_channel_id)
async def fj_add_process(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    """پردازش آیدی کانال برای قفل عضویت."""
    text = message.text.strip()
    channel_id = None
    channel_username = None

    # تلاش برای تبدیل به عدد
    try:
        channel_id = int(text)
    except ValueError:
        # تلاش برای resolve کردن یوزرنیم
        if text.startswith("@"):
            channel_username = text[1:]
        elif text.startswith("https://t.me/"):
            channel_username = text.split("/")[-1]
        else:
            channel_username = text

    # resolve یوزرنیم
    if channel_username and not channel_id:
        try:
            chat = await bot.get_chat(channel_username)
            channel_id = chat.id
        except Exception:
            await message.answer(
                "⚠️ **کانال یافت نشد!**\n\nآیدی عددی صحیح وارد کنید.",
                parse_mode="Markdown",
                reply_markup=cancel_panel_button(),
            )
            return

    if not channel_id:
        await message.answer(
            "⚠️ **آیدی نامعتبر!**\n\nمثال: `-1001234567890`",
            parse_mode="Markdown",
            reply_markup=cancel_panel_button(),
        )
        return

    # گرفتن اطلاعات کانال
    try:
        chat = await bot.get_chat(channel_id)
        title = chat.title
        invite_link = chat.invite_link
    except Exception:
        title = None
        invite_link = None

    await ChannelService.add_channel(
        session=session,
        channel_id=channel_id,
        channel_username=channel_username,
        channel_title=title,
        invite_link=invite_link,
    )

    await state.clear()
    await message.answer(
        f"✅ **کانال به قفل عضویت اضافه شد!**\n\n"
        f"📢 عنوان: {title or 'نامشخص'}\n"
        f"🆔 آیدی: `{channel_id}`",
        parse_mode="Markdown",
        reply_markup=force_join_menu(),
    )
    logger.info(f"Force join channel added: {channel_id} by {message.from_user.id}")


# ── ➖ حذف کانال ───────────────────────────────────


@router.callback_query(F.data == CD.FJ_REMOVE)
async def fj_remove_list(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    """نمایش لیست کانال‌ها برای حذف."""
    if not is_admin:
        return

    channels = await ChannelService.get_all_channels(session)
    if not channels:
        await callback.answer("⚠️ هیچ کانالی وجود ندارد.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for ch in channels:
        status = "✅" if ch.is_active else "❌"
        builder.row(InlineKeyboardButton(
            text=f"🗑 {status} {ch.display_name} ({ch.channel_id})",
            callback_data=f"fj_rm_go:{ch.channel_id}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.SETTINGS_FORCE_JOIN))

    await callback.message.edit_text(
        "➖ **حذف کانال از قفل عضویت**\n\nکانال مورد نظر را انتخاب کنید:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fj_rm_go:"))
async def fj_remove_confirm(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    """تأیید حذف کانال."""
    if not is_admin:
        return

    channel_id = int(callback.data.split(":")[1])
    removed = await ChannelService.remove_channel(session, channel_id)

    if removed:
        await callback.answer(f"✅ کانال {channel_id} حذف شد.", show_alert=True)
    else:
        await callback.answer("⚠️ کانال یافت نشد.", show_alert=True)

    # بروزرسانی لیست
    await fj_remove_list(callback, session, is_admin)


# ── 📋 لیست کانال‌ها ───────────────────────────────


@router.callback_query(F.data == CD.FJ_LIST)
async def fj_list_channels(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    """نمایش لیست کانال‌های قفل عضویت."""
    if not is_admin:
        return

    channels = await ChannelService.get_all_channels(session)

    if not channels:
        text = "📋 **لیست کانال‌های قفل عضویت:**\n\n⚠️ هیچ کانالی تنظیم نشده."
    else:
        text = "📋 **لیست کانال‌های قفل عضویت:**\n\n"
        for i, ch in enumerate(channels, 1):
            status = "✅ فعال" if ch.is_active else "❌ غیرفعال"
            text += (
                f"{i}. {ch.display_name}\n"
                f"   🆔 `{ch.channel_id}`\n"
                f"   📊 {status}\n"
                f"   🔗 {ch.join_link}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.SETTINGS_FORCE_JOIN),
        parse_mode="Markdown",
    )
    await callback.answer()


# ── 🔄 فعال/غیرفعال ────────────────────────────────


@router.callback_query(F.data == CD.FJ_TOGGLE)
async def fj_toggle_list(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    """نمایش لیست کانال‌ها برای toggle."""
    if not is_admin:
        return

    channels = await ChannelService.get_all_channels(session)
    if not channels:
        await callback.answer("⚠️ هیچ کانالی وجود ندارد.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for ch in channels:
        status = "✅" if ch.is_active else "❌"
        toggle_text = "🔴 غیرفعال" if ch.is_active else "🟢 فعال"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {ch.display_name}",
                callback_data="noop",
            ),
            InlineKeyboardButton(
                text=toggle_text,
                callback_data=f"fj_tog_go:{ch.channel_id}",
            ),
        )
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.SETTINGS_FORCE_JOIN))

    await callback.message.edit_text(
        "🔄 **فعال/غیرفعال کردن کانال‌ها**\n\nدکمه مربوط به هر کانال را بزنید:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fj_tog_go:"))
async def fj_toggle_confirm(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    """toggle یک کانال خاص."""
    if not is_admin:
        return

    channel_id = int(callback.data.split(":")[1])
    new_state = await ChannelService.toggle_channel(session, channel_id)

    if new_state is not None:
        status = "فعال" if new_state else "غیرفعال"
        await callback.answer(f"✅ کانال {status} شد.")
    else:
        await callback.answer("⚠️ کانال یافت نشد.", show_alert=True)

    # بروزرسانی
    await fj_toggle_list(callback, session, is_admin)


# ═══════════════════════════════════════════════════════
# ❤️ قفل واکنش (Reaction Lock)
# ═══════════════════════════════════════════════════════


@router.callback_query(F.data == CD.ADV_REACTION)
async def show_reaction_lock(callback: CallbackQuery, is_admin: bool) -> None:
    """نمایش منوی قفل واکنش."""
    if not is_admin:
        return

    await callback.message.edit_text(
        "❤️ **قفل واکنش**\n\nاز منوی زیر عمل مورد نظر را انتخاب کنید:",
        reply_markup=reaction_lock_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ── ➕ افزودن قفل واکنش ───────────────────────────


@router.callback_query(F.data == CD.RL_ADD)
async def rl_add_start(callback: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    """شروع افزودن قفل واکنش."""
    if not is_admin:
        return

    await state.set_state(LockStates.waiting_rl_channel_id)
    await callback.message.edit_text(
        "➕ **افزودن قفل واکنش**\n\n"
        "آیدی عددی کانال حاوی پست را وارد کنید:\n\n"
        "مثال: `-1001234567890`",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(LockStates.waiting_rl_channel_id)
async def rl_add_channel(message: Message, state: FSMContext) -> None:
    """پردازش آیدی کانال قفل واکنش."""
    try:
        channel_id = int(message.text.strip())
        await state.update_data(rl_channel_id=channel_id)
        await state.set_state(LockStates.waiting_rl_message_id)
        await message.answer(
            f"✅ کانال: `{channel_id}`\n\n💬 حالا آیدی پیام مورد نظر را وارد کنید:",
            parse_mode="Markdown",
            reply_markup=cancel_panel_button(),
        )
    except ValueError:
        await message.answer(
            "⚠️ **آیدی نامعتبر!**\n\nیک عدد صحیح وارد کنید.",
            parse_mode="Markdown",
            reply_markup=cancel_panel_button(),
        )


@router.message(LockStates.waiting_rl_message_id)
async def rl_add_message(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """پردازش آیدی پیام و ذخیره قفل واکنش."""
    try:
        message_id = int(message.text.strip())
        data = await state.get_data()
        channel_id = data.get("rl_channel_id")

        await ChannelService.add_reaction_lock(
            session=session,
            channel_id=channel_id,
            message_id=message_id,
        )

        await state.clear()
        await message.answer(
            f"✅ **قفل واکنش اضافه شد!**\n\n"
            f"📢 کانال: `{channel_id}`\n"
            f"💬 پیام: `{message_id}`",
            parse_mode="Markdown",
            reply_markup=reaction_lock_menu(),
        )
        logger.info(f"Reaction lock added: ch={channel_id} msg={message_id}")
    except ValueError:
        await message.answer(
            "⚠️ **آیدی نامعتبر!**\n\nیک عدد صحیح وارد کنید.",
            parse_mode="Markdown",
            reply_markup=cancel_panel_button(),
        )


# ── ➖ حذف قفل واکنش ──────────────────────────────


@router.callback_query(F.data == CD.RL_REMOVE)
async def rl_remove_list(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    """نمایش لیست قفل‌ها برای حذف."""
    if not is_admin:
        return

    locks = await ChannelService.get_all_reaction_locks(session)
    if not locks:
        await callback.answer("⚠️ قفل واکنشی وجود ندارد.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for lock in locks:
        status = "✅" if lock.is_active else "❌"
        builder.row(InlineKeyboardButton(
            text=f"🗑 {status} کانال `{lock.channel_id}` پیام `{lock.message_id}`",
            callback_data=f"rl_rm_go:{lock.id}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=CD.ADV_REACTION))

    await callback.message.edit_text(
        "➖ **حذف قفل واکنش**\n\nقفل مورد نظر را انتخاب کنید:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rl_rm_go:"))
async def rl_remove_confirm(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    """تأیید حذف قفل واکنش."""
    if not is_admin:
        return

    lock_id = int(callback.data.split(":")[1])
    removed = await ChannelService.remove_reaction_lock(session, lock_id)

    if removed:
        await callback.answer("✅ قفل واکنش حذف شد.", show_alert=True)
    else:
        await callback.answer("⚠️ قفل یافت نشد.", show_alert=True)

    await rl_remove_list(callback, session, is_admin)


# ── 📋 لیست قفل‌ها ─────────────────────────────────


@router.callback_query(F.data == CD.RL_LIST)
async def rl_list_locks(callback: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    """نمایش لیست قفل‌های واکنش."""
    if not is_admin:
        return

    locks = await ChannelService.get_all_reaction_locks(session)

    if not locks:
        text = "📋 **لیست قفل‌های واکنش:**\n\n⚠️ قفل واکنشی تنظیم نشده."
    else:
        text = "📋 **لیست قفل‌های واکنش:**\n\n"
        for i, lock in enumerate(locks, 1):
            status = "✅ فعال" if lock.is_active else "❌ غیرفعال"
            emoji = lock.reaction_emoji or "هر واکنشی"
            text += (
                f"{i}. کانال: `{lock.channel_id}`\n"
                f"   💬 پیام: `{lock.message_id}`\n"
                f"   😀 واکنش: {emoji}\n"
                f"   📊 {status}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(CD.ADV_REACTION),
        parse_mode="Markdown",
    )
    await callback.answer()
