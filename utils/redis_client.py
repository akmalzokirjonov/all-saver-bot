"""
Redis async client wrapper.

Key schema:
  user:{uid}:lang                   → str (language code)
  user:{uid}:cookies                → str (Netscape cookie content)
  user:{uid}:files                  → hash {file_key: json_meta}
  stats:downloads                   → int
  stats:errors                      → int
  stats:users                       → HyperLogLog (unique user count)
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from typing import Any, Dict, Optional, cast

import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger(__name__)

# Module-level Redis client (initialised by setup_redis())
_redis: Optional[aioredis.Redis] = None


async def setup_redis() -> aioredis.Redis:
    """Create and test the Redis connection. Call once at startup."""
    global _redis
    _redis = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=10,
        retry_on_timeout=True,
    )
    await _ra().ping()
    logger.info("Redis connected: %s", settings.REDIS_URL)
    return _redis


async def close_redis() -> None:
    """Close Redis connection at shutdown."""
    global _redis
    if _redis:
        await _ra().aclose()
        _redis = None


def _r() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialised. Call setup_redis() first.")
    return _redis


def _ra() -> Any:
    return cast(Any, _r())


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except Exception:
        return default


# ─── Active downloads (cross-process) ────────────────────────────────────────

async def active_download_count(user_id: int) -> int:
    """Return active download count for a user."""
    try:
        val = await _ra().get(f"active:user:{user_id}")
        return _as_int(val, 0)
    except Exception:
        return 0


async def active_total_count() -> int:
    """Return total active downloads across all users."""
    try:
        val = await _ra().get("active:total")
        return _as_int(val, 0)
    except Exception:
        return 0


async def increment_active(user_id: int, ttl_seconds: int) -> None:
    """Increment active download counters with TTL."""
    try:
        r = _ra()
        await r.incr(f"active:user:{user_id}")
        await r.expire(f"active:user:{user_id}", ttl_seconds)
        await r.incr("active:total")
        await r.expire("active:total", ttl_seconds)
    except Exception:
        pass


async def decrement_active(user_id: int) -> None:
    """Decrement active download counters (never below 0)."""
    try:
        r = _ra()
        user_key = f"active:user:{user_id}"
        new_val = await r.decr(user_key)
        if new_val < 0:
            await r.set(user_key, 0)
        new_total = await r.decr("active:total")
        if new_total < 0:
            await r.set("active:total", 0)
    except Exception:
        pass


# ─── Language ─────────────────────────────────────────────────────────────────

async def get_user_lang(user_id: int) -> str:
    try:
        val = await _ra().get(f"user:{user_id}:lang")
        return (val or settings.DEFAULT_LANG) if isinstance(val, str) else settings.DEFAULT_LANG
    except Exception:
        return settings.DEFAULT_LANG


async def has_user_lang(user_id: int) -> bool:
    try:
        val = await _ra().get(f"user:{user_id}:lang")
        return bool(val)
    except Exception:
        return False


async def set_user_lang(user_id: int, lang: str) -> None:
    await _ra().set(f"user:{user_id}:lang", lang)


# ─── Cookies ──────────────────────────────────────────────────────────────────

async def set_user_cookies(user_id: int, content: str) -> None:
    """Store cookie content with 30-day expiry."""
    expire = settings.COOKIE_EXPIRE_DAYS * 86400
    await _ra().set(f"user:{user_id}:cookies", content, ex=expire)


async def get_user_cookies_path(user_id: int) -> Optional[str]:
    """
    Write cookies to a temp file and return path.
    Caller is responsible for deleting the file.
    Returns None if user has no cookies stored.
    """
    try:
        content = await _ra().get(f"user:{user_id}:cookies")
        if not content or not isinstance(content, str):
            return None
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        tmp.write(content)
        tmp.flush()
        tmp.close()
        return tmp.name
    except Exception as e:
        logger.error("Failed to write cookies for user %s: %s", user_id, e)
        return None


async def delete_user_cookies(user_id: int) -> None:
    await _ra().delete(f"user:{user_id}:cookies")


# ─── User files ───────────────────────────────────────────────────────────────

async def save_user_file(user_id: int, file_key: str, meta: dict) -> None:
    """Save file metadata to user's file hash with TTL."""
    r = _ra()
    hash_key = f"user:{user_id}:files"
    expire_secs = settings.FILE_EXPIRE_HOURS * 3600

    await r.hset(hash_key, file_key, json.dumps(meta))
    await r.expire(hash_key, expire_secs)


async def get_user_files(user_id: int) -> Dict[str, dict]:
    """Return all file metadata for user."""
    try:
        raw = await _ra().hgetall(f"user:{user_id}:files")
        result = {}
        for key, val in (raw or {}).items():
            try:
                if isinstance(val, str):
                    result[key] = json.loads(val)
            except json.JSONDecodeError:
                pass
        # Sort by saved_at descending
        return dict(
            sorted(result.items(), key=lambda x: x[1].get("saved_at", 0), reverse=True)
        )
    except Exception as e:
        logger.error("get_user_files failed: %s", e)
        return {}


async def get_user_file(user_id: int, file_key: str) -> Optional[dict]:
    """Return single file metadata."""
    try:
        raw = await _ra().hget(f"user:{user_id}:files", file_key)
        return json.loads(raw) if isinstance(raw, str) and raw else None
    except Exception:
        return None


async def delete_user_file(user_id: int, file_key: str) -> bool:
    """Delete file metadata from Redis and disk."""
    try:
        meta_raw = await _ra().hget(f"user:{user_id}:files", file_key)
        if not meta_raw:
            return False
        meta = json.loads(meta_raw) if isinstance(meta_raw, str) else {}
        # Try to remove disk file
        path = meta.get("path")
        if path:
            try:
                os.remove(path)
            except OSError:
                pass
        await _ra().hdel(f"user:{user_id}:files", file_key)
        return True
    except Exception as e:
        logger.error("delete_user_file failed: %s", e)
        return False


# ─── Statistics ───────────────────────────────────────────────────────────────

async def increment_stat(stat: str) -> None:
    """Increment a stats counter (downloads / errors)."""
    try:
        await _ra().incr(f"stats:{stat}")
    except Exception:
        pass


async def track_user(user_id: int) -> None:
    """Track unique user via HyperLogLog."""
    try:
        await _ra().pfadd("stats:users", str(user_id))
    except Exception:
        pass


async def get_stats() -> Dict[str, Any]:
    """Return stats dict."""
    try:
        r = _ra()
        downloads = _as_int(await r.get("stats:downloads"), 0)
        errors = _as_int(await r.get("stats:errors"), 0)
        users = _as_int(await r.pfcount("stats:users"), 0)
        return {"downloads": downloads, "errors": errors, "users": users}
    except Exception as e:
        logger.error("get_stats failed: %s", e)
        return {"downloads": 0, "errors": 0, "users": 0}
