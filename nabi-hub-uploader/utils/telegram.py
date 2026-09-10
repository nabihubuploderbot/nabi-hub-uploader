"""
utils/telegram.py — Telegram API helper functions.

Fixed: better error handling for membership checks.
"""

from __future__ import annotations

from typing import Optional

from aiogram import Bot
from aiogram.types import ChatMemberOwner, ChatMemberAdministrator, \
    ChatMemberMember, ChatMemberRestricted, ChatMemberLeft, ChatMemberBanned
from loguru import logger


async def check_membership(
    bot: Bot,
    chat_id: int | str,
    user_id: int,
) -> tuple[bool, Optional[str]]:
    """
    Check if a user is a member of a chat/channel.

    Returns:
        Tuple of (is_member: bool, status: str or None).
        If the bot can't check (not admin), returns (True, "skip").
    """
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        status = member.status

        if isinstance(member, (ChatMemberOwner, ChatMemberAdministrator)):
            return True, status
        if isinstance(member, ChatMemberMember):
            return True, status
        if isinstance(member, ChatMemberRestricted):
            return member.is_member, status
        if isinstance(member, (ChatMemberLeft, ChatMemberBanned)):
            return False, status

        return False, status

    except Exception as e:
        error_str = str(e).lower()
        # اگر بات ادمین کانال نیست، خطا میده
        # در این حالت نمیتونیم عضویت رو چک کنیم
        # پس عضویت رو تأیید می‌کنیم تا کاربر گیر نکنه
        if "not enough rights" in error_str or "not member" in error_str or "admin" in error_str or "chat not found" in error_str:
            logger.warning(
                f"⚠️ Cannot check membership in {chat_id}: Bot is not admin! "
                f"Make the bot an admin in the channel to enable force join check."
            )
            # بات نمیتونه چک کنه → عضویت رو تأیید کن
            return True, "skip"
        logger.error(f"Failed to check membership for user {user_id} in {chat_id}: {e}")
        return False, None


async def check_all_memberships(
    bot: Bot,
    user_id: int,
    channels: list[dict],
) -> tuple[bool, list[dict]]:
    """
    Check user membership across multiple channels.

    Returns:
        Tuple of (all_joined: bool, details: list of dicts).
    """
    results = []
    all_joined = True

    for ch in channels:
        is_member, status = await check_membership(
            bot=bot, chat_id=ch["channel_id"], user_id=user_id,
        )
        results.append({
            "channel_id": ch["channel_id"],
            "channel_title": ch.get("channel_title", str(ch["channel_id"])),
            "join_link": ch.get("join_link", "#"),
            "is_member": is_member,
            "status": status,
        })
        if not is_member:
            all_joined = False

    return all_joined, results


async def get_chat_info(bot: Bot, chat_id: int | str) -> Optional[dict]:
    """Get basic information about a chat."""
    try:
        chat = await bot.get_chat(chat_id=chat_id)
        return {
            "id": chat.id, "type": chat.type, "title": chat.title,
            "username": chat.username, "description": chat.description,
            "invite_link": chat.invite_link,
        }
    except Exception as e:
        logger.error(f"Failed to get chat info for {chat_id}: {e}")
        return None


def get_file_type(message) -> Optional[str]:
    if message.document: return "document"
    if message.photo: return "photo"
    if message.video: return "video"
    if message.audio: return "audio"
    if message.voice: return "voice"
    if message.video_note: return "video_note"
    if message.animation: return "animation"
    if message.sticker: return "sticker"
    return None


def get_file_id_and_unique_id(message) -> tuple[Optional[str], Optional[str]]:
    if message.document: return message.document.file_id, message.document.file_unique_id
    if message.photo:
        photo = message.photo[-1]
        return photo.file_id, photo.file_unique_id
    if message.video: return message.video.file_id, message.video.file_unique_id
    if message.audio: return message.audio.file_id, message.audio.file_unique_id
    if message.voice: return message.voice.file_id, message.voice.file_unique_id
    if message.video_note: return message.video_note.file_id, message.video_note.file_unique_id
    if message.animation: return message.animation.file_id, message.animation.file_unique_id
    return None, None


def get_file_size(message) -> int:
    if message.document: return message.document.file_size or 0
    if message.photo: return message.photo[-1].file_size or 0
    if message.video: return message.video.file_size or 0
    if message.audio: return message.audio.file_size or 0
    if message.voice: return message.voice.file_size or 0
    if message.video_note: return message.video_note.file_size or 0
    if message.animation: return message.animation.file_size or 0
    return 0


def get_file_name(message) -> Optional[str]:
    if message.document: return message.document.file_name
    if message.video: return message.video.file_name
    if message.audio: return message.audio.file_name
    return None


def get_mime_type(message) -> Optional[str]:
    if message.document: return message.document.mime_type
    if message.video: return message.video.mime_type
    if message.audio: return message.audio.mime_type
    if message.voice: return message.voice.mime_type
    if message.animation: return message.animation.mime_type
    return None
