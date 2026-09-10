"""توابع کمکی / Small helpers."""
import secrets
import string
from datetime import datetime, timezone

ALPHABET = string.ascii_lowercase + string.digits


def generate_code(length: int = 10) -> str:
    """تولید کد یکتا برای فایل/آلبوم / Generate unique file/album code."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def human_size(num: float) -> str:
    """تبدیل بایت به خوانا / Human readable size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}"
    num *= 1024.0
    return f"{num:.1f} PB"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def file_type_of(message_file) -> str:
    """تشخیص نوع فایل از آبجکت پیام / Detect file type from message."""
    if message_file.photo:
        return "photo"
    if message_file.video:
        return "video"
    if message_file.audio:
        return "audio"
    if message_file.voice:
        return "voice"
    if message_file.video_note:
        return "video_note"
    if message_file.animation:
        return "animation"
    return "document"


def extract_file(message_file):
    """استخراج (file_id, size, name) از پیام / Extract ids from message."""
    if message_file.photo:
        return message_file.photo[-1].file_id, message_file.photo[-1].file_size or 0, None
    if message_file.video:
        return message_file.video.file_id, message_file.video.file_size or 0, message_file.video.file_name
    if message_file.audio:
        return message_file.audio.file_id, message_file.audio.file_size or 0, message_file.audio.file_name
    if message_file.voice:
        return message_file.voice.file_id, message_file.voice.file_size or 0, None
    if message_file.video_note:
        return message_file.video_note.file_id, message_file.video_note.file_size or 0, None
    if message_file.animation:
        return message_file.animation.file_id, message_file.animation.file_size or 0, message_file.animation.file_name
    if message_file.document:
        return (
            message_file.document.file_id,
            message_file.document.file_size or 0,
            message_file.document.file_name,
        )
    return None, 0, None
