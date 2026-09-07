"""
utils/telegram.py — Telegram API helper functions.

Utility functions for interacting with the Telegram Bot API
outside of the standard handler flow.
"""

from __future__ import annotations

from typing import Optional

from aiogram import Bot
from aiogram.types import ChatMember, ChatMemberOwner, ChatMemberAdministrator, \
    ChatMemberMember, ChatMemberRestricted, ChatMemberLeft, ChatMemberBanned
from loguru import logger


async def check_membership(
    bot: Bot,
    chat_id: int | str,
    user_id: int,
) -> tuple[bool, Optional[str]]:
    """
    Check if a user is a member of a chat/channel.

    Args:
        bot: Bot instance.
        chat_id: Channel or group ID.
        user_id: User's Telegram ID.

    Returns:
        Tuple of (is_member: bool, status: str or None).
    """
    try:
        member: ChatMember = await bot.get_chat_member(
            chat_id=chat_id,
            user_id=user_id,
        )
        status = member.status
        is_member = status in (
            ChatMemberOwner.status,
            ChatMemberAdministrator.status,
            ChatMemberMember.status,
            ChatMemberRestricted.status,  # restricted can still be "member"
        )
        # For restricted members, check if they can_send_messages
        if isinstance(member, ChatMemberRestricted):
            is_member = member.is_member

        return is_member, status

    except Exception as e:
        logger.error(f"Failed to check membership for user {user_id} in {chat_id}: {e}")
        return False, None


async def check_all_memberships(
    bot: Bot,
    user_id: int,
    channels: list[dict],
) -> tuple[bool, list[dict]]:
    """
    Check user membership across multiple channels.

    Args:
        bot: Bot instance.
        user_id: User's Telegram ID.
        channels: List of channel dicts with 'channel_id' key.

    Returns:
        Tuple of (all_joined: bool, details: list of dicts with channel info and status).
    """
    results = []
    all_joined = True

    for ch in channels:
        is_member, status = await check_membership(
            bot=bot,
            chat_id=ch["channel_id"],
            user_id=user_id,
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
    """
    Get basic information about a chat.

    Args:
        bot: Bot instance.
        chat_id: Chat ID or username.

    Returns:
        Dict with chat info or None on failure.
    """
    try:
        chat = await bot.get_chat(chat_id=chat_id)
        return {
            "id": chat.id,
            "type": chat.type,
            "title": chat.title,
            "username": chat.username,
            "description": chat.description,
            "invite_link": chat.invite_link,
        }
    except Exception as e:
        logger.error(f"Failed to get chat info for {chat_id}: {e}")
        return None


def get_file_type(message) -> Optional[str]:
    """
    Determine the type of file in a message.

    Args:
        message: aiogram Message object.

    Returns:
        File type string or None.
    """
    if message.document:
        return "document"
    if message.photo:
        return "photo"
    if message.video:
        return "video"
    if message.audio:
        return "audio"
    if message.voice:
        return "voice"
    if message.video_note:
        return "video_note"
    if message.animation:
        return "animation"
    if message.sticker:
        return "sticker"
    return None


def get_file_id_and_unique_id(message) -> tuple[Optional[str], Optional[str]]:
    """
    Extract file_id and file_unique_id from a message.

    Args:
        message: aiogram Message object.

    Returns:
        Tuple of (file_id, file_unique_id).
    """
    if message.document:
        return message.document.file_id, message.document.file_unique_id
    if message.photo:
        # Photo is a list; get the largest size
        photo = message.photo[-1]
        return photo.file_id, photo.file_unique_id
    if message.video:
        return message.video.file_id, message.video.file_unique_id
    if message.audio:
        return message.audio.file_id, message.audio.file_unique_id
    if message.voice:
        return message.voice.file_id, message.voice.file_unique_id
    if message.video_note:
        return message.video_note.file_id, message.video_note.file_unique_id
    if message.animation:
        return message.animation.file_id, message.animation.file_unique_id
    return None, None


def get_file_size(message) -> int:
    """Get file size from a message."""
    if message.document:
        return message.document.file_size or 0
    if message.photo:
        return message.photo[-1].file_size or 0
    if message.video:
        return message.video.file_size or 0
    if message.audio:
        return message.audio.file_size or 0
    if message.voice:
        return message.voice.file_size or 0
    if message.video_note:
        return message.video_note.file_size or 0
    if message.animation:
        return message.animation.file_size or 0
    return 0


def get_file_name(message) -> Optional[str]:
    """Get original file name from a message."""
    if message.document:
        return message.document.file_name
    if message.video:
        return message.video.file_name
    if message.audio:
        return message.audio.file_name
    return None


def get_mime_type(message) -> Optional[str]:
    """Get MIME type from a message."""
    if message.document:
        return message.document.mime_type
    if message.video:
        return message.video.mime_type
    if message.audio:
        return message.audio.mime_type
    if message.voice:
        return message.voice.mime_type
    if message.animation:
        return message.animation.mime_type
    return None
