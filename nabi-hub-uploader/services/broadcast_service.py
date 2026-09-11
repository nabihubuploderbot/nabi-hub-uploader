"""
services/broadcast_service.py — Broadcast queue management with Redis.

Handles broadcasting messages to all users with progress tracking.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Optional

import redis.asyncio as aioredis
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from models.broadcast import BroadcastLog
from models.user import User
from services.user_service import UserService


class BroadcastService:
    """Manages broadcast operations using Redis queue."""

    QUEUE_KEY = "nabi:broadcast:queue"
    STATUS_KEY = "nabi:broadcast:status"
    CANCEL_KEY = "nabi:broadcast:cancel"

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def enqueue_broadcast(
        self,
        session: AsyncSession,
        admin_id: int,
        message_data: dict,
    ) -> int:
        """
        Add a broadcast to the queue.

        Args:
            session: Database session.
            admin_id: Admin user ID.
            message_data: Dict with message content (text, media, etc.).

        Returns:
            Broadcast log ID.
        """
        # Get all active user IDs
        user_ids = await UserService.get_active_user_ids(session)

        # Create broadcast log
        log = BroadcastLog(
            admin_id=admin_id,
            message_text=message_data.get("text"),
            media_file_id=message_data.get("media_file_id"),
            media_type=message_data.get("media_type"),
            is_forward=message_data.get("is_forward", False),
            source_chat_id=message_data.get("source_chat_id"),
            source_message_id=message_data.get("source_message_id"),
            total_users=len(user_ids),
            status="pending",
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)

        # Push user IDs to Redis queue
        queue_data = {
            "broadcast_id": log.id,
            "user_ids": user_ids,
            "message_data": message_data,
        }
        await self.redis.rpush(self.QUEUE_KEY, json.dumps(queue_data))

        # Update status
        log.status = "running"
        await session.commit()

        logger.info(
            f"Broadcast {log.id} queued: {len(user_ids)} users, "
            f"admin={admin_id}"
        )
        return log.id

    async def update_progress(
        self,
        session: AsyncSession,
        broadcast_id: int,
        success: int = 0,
        fail: int = 0,
        blocked: int = 0,
    ) -> None:
        """Update broadcast progress in database."""
        stmt = (
            BroadcastLog.__table__.update()
            .where(BroadcastLog.id == broadcast_id)
            .values(
                success_count=BroadcastLog.success_count + success,
                fail_count=BroadcastLog.fail_count + fail,
                block_count=BroadcastLog.block_count + blocked,
            )
        )
        await session.execute(stmt)
        await session.commit()

    async def complete_broadcast(
        self,
        session: AsyncSession,
        broadcast_id: int,
    ) -> None:
        """Mark a broadcast as completed."""
        from sqlalchemy import update as sa_update
        stmt = (
            sa_update(BroadcastLog)
            .where(BroadcastLog.id == broadcast_id)
            .values(status="completed")
        )
        await session.execute(stmt)
        await session.commit()

    async def cancel_broadcast(self) -> None:
        """Signal cancellation for the current broadcast."""
        await self.redis.set(self.CANCEL_KEY, "1", ex=300)

    async def is_cancelled(self) -> bool:
        """Check if broadcast was cancelled."""
        result = await self.redis.get(self.CANCEL_KEY)
        return result is not None

    async def clear_cancel(self) -> None:
        """Clear the cancel flag."""
        await self.redis.delete(self.CANCEL_KEY)

    async def get_queue_length(self) -> int:
        """Get number of pending items in broadcast queue."""
        return await self.redis.llen(self.QUEUE_KEY) or 0

    async def get_broadcast_stats(
        self,
        session: AsyncSession,
        limit: int = 10,
    ) -> list[BroadcastLog]:
        """Get recent broadcast logs."""
        from sqlalchemy import select
        stmt = (
            select(BroadcastLog)
            .order_by(BroadcastLog.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
