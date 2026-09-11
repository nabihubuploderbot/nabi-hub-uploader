"""
utils/helpers.py — General-purpose helper functions.
"""

from __future__ import annotations

import asyncio
import functools
import html
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

from loguru import logger

F = TypeVar("F", bound=Callable[..., Any])


def escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram HTML parse mode."""
    return html.escape(text, quote=False)


def mention_html(user_id: int, name: str) -> str:
    """Create an HTML mention link."""
    return f'<a href="tg://user?id={user_id}">{escape_html(name)}</a>'


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime object as a string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(fmt)


def human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    if size_bytes < 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def human_number(num: int) -> str:
    """Format a number with commas for readability."""
    return f"{num:,}"


def truncate(text: str, max_len: int = 100, suffix: str = "...") -> str:
    """Truncate text to max_len characters."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def chunk_list(lst: list, chunk_size: int) -> list[list]:
    """Split a list into chunks of chunk_size."""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid HTTP/HTTPS URL."""
    return url.startswith(("http://", "https://")) and len(url) > 10


def retry_async(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry an async function on exception.

    Args:
        max_retries: Maximum number of retry attempts.
        delay: Seconds to wait between retries.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exc  # type: ignore

        return wrapper  # type: ignore

    return decorator


def timestamp_now() -> int:
    """Return current Unix timestamp."""
    return int(datetime.now(timezone.utc).timestamp())
