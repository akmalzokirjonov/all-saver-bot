"""
Download queue and concurrency management.

Uses asyncio Semaphores:
  - Per-user semaphore: max MAX_CONCURRENT_PER_USER simultaneous downloads
  - Global semaphore: max MAX_GLOBAL_CONCURRENT simultaneous downloads across all users

Redis is used to track active download counts (cross-process).
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from config import settings
from utils.redis_client import (
    active_download_count,
    active_total_count,
    decrement_active,
    increment_active,
)

logger = logging.getLogger(__name__)

# Global semaphore (total across all users)
_GLOBAL_SEM = asyncio.Semaphore(settings.MAX_GLOBAL_CONCURRENT)

# Per-user semaphore storage
_USER_SEMS: dict[int, asyncio.Semaphore] = defaultdict(
    lambda: asyncio.Semaphore(settings.MAX_CONCURRENT_PER_USER)
)

async def get_active_count(user_id: int) -> int:
    """Return number of active downloads for a user."""
    return await active_download_count(user_id)


async def get_total_active() -> int:
    """Return total active downloads across all users."""
    return await active_total_count()


@asynccontextmanager
async def acquire_slot(user_id: int) -> AsyncGenerator[bool, None]:
    """
    Async context manager that acquires both per-user and global slots.

    Usage::

        async with acquire_slot(user_id) as acquired:
            if not acquired:
                # too many downloads for this user
                return
            await do_download()

    Yields True if slot acquired, False if user is at limit.
    """
    user_sem = _USER_SEMS[user_id]

    async with user_sem:
        async with _GLOBAL_SEM:
            try:
                await increment_active(user_id, settings.ACTIVE_DOWNLOAD_TTL_SECONDS)
                yield True
            finally:
                await decrement_active(user_id)
