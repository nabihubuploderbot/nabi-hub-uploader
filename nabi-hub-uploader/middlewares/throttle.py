"""
middlewares/throttle.py — Rate limiting middleware using Redis.

Prevents users from flooding the bot with requests.
"""

from __future__ import annotations

import time
from typing import Callable, Dict, Any, Awaitable

import redis.asyncio as aioredis
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger


class ThrottleMiddleware(BaseMiddleware):
    """
    Rate limiting middleware.

    Uses Redis to track request timestamps per user.
    Blocks requests that exceed the rate limit.

    Args:
        redis: Async Redis client.
        rate_limit: Maximum requests per time window (default: 5).
        time_window: Time window in seconds (default: 3).
    """

    def __init__(
        self,
        redis: aioredis.Redis,
        rate_limit: int = 5,
        time_window: int = 3,
    ):
        super().__init__()
        self.redis = redis
        self.rate_limit = rate_limit
        self.time_window = time_window

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Extract user_id
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        if user_id is None:
            return await handler(event, data)

        key = f"throttle:{user_id}"
        now = time.time()

        try:
            # Get current request timestamps
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - self.time_window)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self.time_window)
            results = await pipe.execute()

            request_count = results[2]

            if request_count > self.rate_limit:
                logger.warning(
                    f"Rate limit exceeded: user_id={user_id} "
                    f"count={request_count}/{self.rate_limit}"
                )
                if isinstance(event, Message):
                    await event.answer(
                        "⚠️ درخواست‌های شما بیش از حد مجاز است. "
                        "لطفاً کمی صبر کنید."
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "⚠️ لطفاً کمی صبر کنید.",
                        show_alert=True,
                    )
                return  # Don't call the handler

        except Exception as e:
            # If Redis is down, allow the request
            logger.error(f"Throttle middleware error (Redis): {e}")

        return await handler(event, data)
