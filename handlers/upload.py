"""
User file upload handler.

Accepts video, audio, and document files.
Stores metadata in Redis (expires after FILE_EXPIRE_HOURS).
"""
from __future__ import annotations

import logging
import os
import time
import uuid

import aiofiles
from aiogram import F, Router
from aiogram.types import Audio, Document, Message, Video

from config import settings
from utils.i18n import get_text
from utils.redis_client import get_user_lang, save_user_file

logger = logging.getLogger(__name__)
router = Router(name="upload")

_MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


# ─── Video ────────────────────────────────────────────────────────────────────

@router.message(F.video)
async def handle_video_upload(message: Message) -> None:
    await _handle_upload(message, message.video, "video")


# ─── Audio ────────────────────────────────────────────────────────────────────

@router.message(F.audio)
async def handle_audio_upload(message: Message) -> None:
    await _handle_upload(message, message.audio, "audio")


# ─── Document ────────────────────────────────────────────────────────────────

@router.message(F.document)
async def handle_document_upload(message: Message) -> None:
    doc = message.document
    # Only handle media-like documents (video/audio by MIME)
    if doc.mime_type and (
        doc.mime_type.startswith("video/")
        or doc.mime_type.startswith("audio/")
    ):
        await _handle_upload(message, doc, "document")
    # Otherwise ignore (could be cookies file handled by cookies handler)


# ─── Core upload logic ────────────────────────────────────────────────────────

async def _handle_upload(message: Message, media, media_type: str) -> None:
    lang = await get_user_lang(message.from_user.id)

    # Size check
    size = getattr(media, "file_size", 0) or 0
    if size > settings.MAX_FILE_SIZE_BYTES:
        await message.answer(
            get_text("upload_too_large", lang, max=settings.MAX_FILE_SIZE_MB)
        )
        return


    # Download to local storage
    file_key = str(uuid.uuid4())
    ext = _get_extension(media)
    dest_path = os.path.join(settings.DOWNLOAD_DIR, f"upload_{file_key}{ext}")

    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)

    try:
        await message.bot.download(media, destination=dest_path)
    except Exception as e:
        logger.error("Failed to download upload from user %s: %s", message.from_user.id, e)
        await message.answer("❌ Failed to save your file.")
        return

    # Determine display name
    name = (
        getattr(media, "file_name", None)
        or getattr(media, "title", None)
        or f"{media_type}_{file_key[:8]}{ext}"
    )

    # Save metadata to Redis
    meta = {
        "file_id": media.file_id,
        "file_unique_id": media.file_unique_id,
        "name": name,
        "size": size,
        "type": media_type,
        "path": dest_path,
        "saved_at": time.time(),
    }

    await save_user_file(message.from_user.id, file_key, meta)

    await message.answer(
        get_text("upload_saved", lang, name=name),
        parse_mode="HTML",
    )
    logger.info(
        "User %s uploaded %s file: %s (%d bytes)",
        message.from_user.id, media_type, name, size
    )


# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_extension(media) -> str:
    mime = getattr(media, "mime_type", "") or ""
    if "mp4" in mime or "video" in mime:
        return ".mp4"
    if "mp3" in mime or "mpeg" in mime:
        return ".mp3"
    if "ogg" in mime:
        return ".ogg"
    if "m4a" in mime:
        return ".m4a"
    fn = getattr(media, "file_name", "") or ""
    if "." in fn:
        return "." + fn.rsplit(".", 1)[1]
    return ".bin"
