"""
Throttling middleware for aiogram 3.x.

Limits:
  - 1 message per user per 0.5 seconds (flood protection)
  - Max concurrent downloads tracked via queue.py
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)

# Minimum interval between messages from the same user (seconds)
_MIN_INTERVAL = 0.5
# Cleanup stale entries every N messages
_CLEANUP_INTERVAL = 1000
# Remove entries older than this (seconds)
_STALE_THRESHOLD = 300


class ThrottlingMiddleware(BaseMiddleware):
    """Rate-limit incoming messages to prevent spam."""

    def __init__(self, min_interval: float = _MIN_INTERVAL):
        self._min_interval = min_interval
        self._last_message: dict[int, float] = defaultdict(float)
        self._msg_count = 0
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            uid = event.from_user.id
            now = time.monotonic()
            last = self._last_message[uid]

            if now - last < self._min_interval:
                logger.debug("Throttled user %s", uid)
                return  # silently drop

            self._last_message[uid] = now

            # Periodic cleanup to prevent memory leak
            self._msg_count += 1
            if self._msg_count >= _CLEANUP_INTERVAL:
                self._msg_count = 0
                cutoff = now - _STALE_THRESHOLD
                stale = [k for k, v in self._last_message.items() if v < cutoff]
                for k in stale:
                    del self._last_message[k]

        return await handler(event, data)
