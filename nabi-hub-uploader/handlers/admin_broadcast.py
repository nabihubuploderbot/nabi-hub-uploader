"""
admin_broadcast.py — ارسال همگانی

همه پیام‌ها دکمه اینلاین دارن ✅
"""

from __future__ import annotations

import asyncio
from typing import Callable

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings
from services.broadcast_service import BroadcastService
from services.user_service import UserService
from services.setting_service import SettingService
from keyboards.inline import (
    CD,
    broadcast_confirm_keyboard,
    admin_broadcast_menu,
    panel_button,
    back_button,
)
from keyboards.reply import admin_reply_menu, remove_keyboard

router = Router(name="admin_broadcast")


class BroadcastStates(StatesGroup):
    waiting_text = State()
    waiting_media = State()
    waiting_forward = State()
    waiting_confirm = State()


@router.callback_query(F.data == CD.BROADCAST_TEXT)
async def start_text_broadcast(callback: CallbackQuery, state: FSMContext, is_admin: bool, t: Callable[[str], str]) -> None:
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return
    await state.set_state(BroadcastStates.waiting_text)
    await callback.message.edit_text(
        "📝 **ارسال همگانی متن**\n\nپیام مورد نظر را بنویسید:",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_text)
async def receive_broadcast_text(message: Message, state: FSMContext, session: AsyncSession, t: Callable[[str], str]) -> None:
    await state.update_data(broadcast_text=message.html_text or message.text, broadcast_type="text")
    users_count = await UserService.count_users(session)
    await state.set_state(BroadcastStates.waiting_confirm)
    await message.answer(
        f"📨 **پیش‌نمایش:**\n\n{message.html_text or message.text}\n\n👥 کاربران: **{users_count:,}**",
        reply_markup=broadcast_confirm_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CD.BROADCAST_MEDIA)
async def start_media_broadcast(callback: CallbackQuery, state: FSMContext, is_admin: bool, t: Callable[[str], str]) -> None:
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return
    await state.set_state(BroadcastStates.waiting_media)
    await callback.message.edit_text(
        "🖼 **ارسال همگانی رسانه**\n\nفایل رسانه‌ای همراه با کپشن ارسال کنید.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_media, F.content_type.in_({"photo", "video", "document", "audio", "voice", "animation"}))
async def receive_broadcast_media(message: Message, state: FSMContext, session: AsyncSession, t: Callable[[str], str]) -> None:
    media_type = None
    media_file_id = None
    if message.photo:
        media_type, media_file_id = "photo", message.photo[-1].file_id
    elif message.video:
        media_type, media_file_id = "video", message.video.file_id
    elif message.document:
        media_type, media_file_id = "document", message.document.file_id
    elif message.audio:
        media_type, media_file_id = "audio", message.audio.file_id
    elif message.voice:
        media_type, media_file_id = "voice", message.voice.file_id
    elif message.animation:
        media_type, media_file_id = "animation", message.animation.file_id

    if not media_type:
        await message.answer("⚠️ نوع فایل پشتیبانی نمی‌شود.", reply_markup=panel_button())
        return

    await state.update_data(media_type=media_type, media_file_id=media_file_id, broadcast_caption=message.caption or "", broadcast_type="media")
    users_count = await UserService.count_users(session)
    await state.set_state(BroadcastStates.waiting_confirm)
    await message.answer(
        f"📨 **ارسال رسانه**\n\n📦 نوع: {media_type}\n📝 کپشن: {message.caption or '(بدون)'}\n\n👥 کاربران: **{users_count:,}**",
        reply_markup=broadcast_confirm_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == CD.BROADCAST_FORWARD)
async def start_forward_broadcast(callback: CallbackQuery, state: FSMContext, is_admin: bool, t: Callable[[str], str]) -> None:
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return
    await state.set_state(BroadcastStates.waiting_forward)
    await callback.message.edit_text(
        "⏩ **فوروارد همگانی**\n\nپیام را از کانال/گروه فوروارد کنید.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_forward, F.forward_origin)
async def receive_forward_broadcast(message: Message, state: FSMContext, session: AsyncSession, t: Callable[[str], str]) -> None:
    await state.update_data(
        forward_chat_id=message.forward_from_chat.id if message.forward_from_chat else None,
        forward_message_id=message.forward_from_message_id,
        broadcast_type="forward",
    )
    users_count = await UserService.count_users(session)
    await state.set_state(BroadcastStates.waiting_confirm)
    await message.answer(
        f"📨 **فوروارد همگانی**\n\nاز: {message.forward_from_chat.title if message.forward_from_chat else 'N/A'}\n\n👥 کاربران: **{users_count:,}**",
        reply_markup=broadcast_confirm_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == CD.BROADCAST_CONFIRM, BroadcastStates.waiting_confirm)
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot, is_admin: bool, t: Callable[[str], str]) -> None:
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return
    data = await state.get_data()
    broadcast_type = data.get("broadcast_type")
    await state.clear()
    user_ids = await UserService.get_active_user_ids(session)
    total = len(user_ids)
    await callback.message.edit_text(t("broadcast_started", total=total), parse_mode="Markdown")
    await callback.answer()

    success = fail = blocked = 0
    for i, user_id in enumerate(user_ids):
        try:
            if broadcast_type == "text":
                await bot.send_message(chat_id=user_id, text=data.get("broadcast_text", ""), parse_mode="HTML")
            elif broadcast_type == "media":
                mt, fid = data.get("media_type"), data.get("media_file_id")
                cap = data.get("broadcast_caption", "")
                if mt == "photo":
                    await bot.send_photo(user_id, fid, caption=cap)
                elif mt == "video":
                    await bot.send_video(user_id, fid, caption=cap)
                elif mt == "document":
                    await bot.send_document(user_id, fid, caption=cap)
                elif mt == "audio":
                    await bot.send_audio(user_id, fid, caption=cap)
                elif mt == "voice":
                    await bot.send_voice(user_id, fid, caption=cap)
                elif mt == "animation":
                    await bot.send_animation(user_id, fid, caption=cap)
            elif broadcast_type == "forward":
                await bot.forward_message(chat_id=user_id, from_chat_id=data.get("forward_chat_id"), message_id=data.get("forward_message_id"))
            success += 1
        except Exception as e:
            if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                blocked += 1
                await UserService.ban_user(session, user_id)
            else:
                fail += 1
        if i % 25 == 0 and i > 0:
            await asyncio.sleep(1)
            try:
                progress = ((success + fail + blocked) / total) * 100 if total > 0 else 0
                await callback.message.edit_text(
                    t("broadcast_progress", success=success, fail=fail, blocked=blocked, total=total, percent=f"{progress:.1f}"),
                    parse_mode="Markdown",
                )
            except Exception:
                pass

    await callback.message.edit_text(
        t("broadcast_completed", success=success, fail=fail, blocked=blocked),
        reply_markup=panel_button(),
        parse_mode="Markdown",
    )
    logger.info(f"Broadcast done: success={success} fail={fail} blocked={blocked} total={total}")


@router.callback_query(F.data == CD.BROADCAST_CANCEL)
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext, is_admin: bool, t: Callable[[str], str]) -> None:
    if not is_admin:
        await callback.answer(t("no_permission"), show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        t("broadcast_cancelled"),
        reply_markup=admin_broadcast_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()
