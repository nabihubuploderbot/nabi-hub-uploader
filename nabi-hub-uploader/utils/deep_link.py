"""
utils/deep_link.py — Deep link generation and parsing.

Generates short, unique tokens for file deep links.
Format: /start FILE_TOKEN
"""

from __future__ import annotations

import hashlib
import secrets
import string
import time
from typing import Optional


# Characters used in tokens (URL-safe, no ambiguous chars)
_TOKEN_CHARS = string.ascii_letters + string.digits  # a-zA-Z0-9
_TOKEN_LENGTH = 12


def generate_token(length: int = _TOKEN_LENGTH) -> str:
    """
    Generate a cryptographically random token.

    Args:
        length: Token length (default 12).

    Returns:
        Random token string.
    """
    return "".join(secrets.choice(_TOKEN_CHARS) for _ in range(length))


def generate_file_token(file_id: int, file_unique_id: str) -> str:
    """
    Generate a deterministic short token for a file.

    Uses a hash of file data + random salt to avoid collisions
    while keeping tokens reasonably short.

    Args:
        file_id: Database file ID.
        file_unique_id: Telegram file_unique_id.

    Returns:
        Short token string.
    """
    # Use secrets for randomness + hash for uniformity
    salt = secrets.token_hex(4)
    raw = f"{file_id}:{file_unique_id}:{salt}:{time.time_ns()}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    # Take first N characters
    return digest[:_TOKEN_LENGTH]


def validate_token(token: str) -> bool:
    """
    Validate that a token has the expected format.

    Args:
        token: Token string to validate.

    Returns:
        True if token format is valid.
    """
    if not token or len(token) != _TOKEN_LENGTH:
        return False
    return all(c in _TOKEN_CHARS for c in token)


def extract_start_payload(args: list[str]) -> Optional[str]:
    """
    Extract the deep link payload from /start command arguments.

    Args:
        args: Command arguments (e.g., ["FILE_TOKEN"]).

    Returns:
        The payload string, or None if not present.
    """
    if args and len(args) > 0:
        payload = args[0].strip()
        if validate_token(payload):
            return payload
    return None
