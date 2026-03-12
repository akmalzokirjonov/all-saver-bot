"""
Download handler: detects URLs → quality keyboard → download → send.

Flow:
  1. User sends message with URL
  2. Bot extracts URL, fetches title, shows quality keyboard
  3. User selects quality (callback_query)
  4. Bot downloads with progress updates via edited message
  5. Bot sends file (or external link if >50 MB)
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import time
from typing import Optional

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    Message,
)

from config import settings
from keyboards import quality_keyboard
from download_queue import acquire_slot, get_active_count, get_total_active
from states import DownloadState
from utils.compressor import compress_video, extract_audio
from utils.downloader import (
    Downloader,
    DownloadProgress,
    DownloadResult,
    extract_url,
)
from utils.i18n import get_text
from utils.redis_client import (
    get_user_cookies_path,
    get_user_lang,
    increment_stat,
    track_user,
)
from utils.uploader import upload_file

logger = logging.getLogger(__name__)
router = Router(name="download")

# Minimum interval between progress message edits (seconds)
_PROGRESS_INTERVAL = 3.0


# ─── URL detection ────────────────────────────────────────────────────────────

@router.message(F.text)
async def handle_text(message: Message, state: FSMContext) -> None:
    """Detect URLs in incoming text messages."""
    user = message.from_user
    if not user:
        return
    url = extract_url(message.text or "")
    if not url:
        return  # not a URL, ignore (other handlers may pick this up)

    lang = await get_user_lang(user.id)
    user_id = user.id

    # Check concurrent download limit
    active = await get_active_count(user_id)
    total_active = await get_total_active()
    if active >= settings.MAX_CONCURRENT_PER_USER:
        await message.answer(
            get_text("too_many_downloads", lang, n=active),
            parse_mode="HTML",
        )
        return
    if total_active >= settings.MAX_GLOBAL_CONCURRENT:
        await message.answer(
            get_text("server_busy", lang),
            parse_mode="HTML",
        )
        return

    # Fetch video title in background (non-blocking)
    title = await _get_title(url, user_id)

    await state.update_data(download_url=url)
    await state.set_state(DownloadState.waiting_quality)

    # Show quality keyboard
    await message.answer(
        get_text("choose_quality", lang, title=title),
        reply_markup=quality_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


# ─── Quality selection callback ───────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith("q:"))
async def handle_quality_choice(call: CallbackQuery, state: FSMContext) -> None:
    user = call.from_user
    if not user:
        return
    data = call.data or ""  # format: "q:<quality>|<url>"
    if not data:
        return

    msg = call.message if isinstance(call.message, Message) else None
    if not msg:
        await call.answer("Message unavailable", show_alert=True)
        return

    if data == "q:cancel":
        lang = await get_user_lang(user.id)
        await msg.edit_text(get_text("cancelled", lang))
        await state.clear()
        await call.answer()
        return

    # Parse quality
    quality = data[2:] if data.startswith("q:") else ""
    
    state_data = await state.get_data()
    url = state_data.get("download_url")
    if not url:
        await call.answer("Session expired. Please send the link again.", show_alert=True)
        return

    user_id = user.id
    lang = await get_user_lang(user_id)

    await state.clear()
    await call.answer("⏳ Starting download…")

    # Replace keyboard with progress message
    edited = await msg.edit_text(
        get_text("downloading", lang, percent=0, bar="░" * 10, speed="—", eta="—"),
        parse_mode="HTML",
    )
    status_msg = edited if isinstance(edited, Message) else msg

    await _run_download(
        bot=call.bot,
        user_id=user_id,
        url=url,
        quality=quality,
        lang=lang,
        status_msg=status_msg,
    )


# ─── Core download runner ─────────────────────────────────────────────────────

async def _run_download(
    bot,
    user_id: int,
    url: str,
    quality: str,
    lang: str,
    status_msg: Message,
) -> None:
    """Acquire slot, run download, handle result."""

    async with acquire_slot(user_id) as acquired:
        if not acquired:
            active = await get_active_count(user_id)
            total_active = await get_total_active()
            if active >= settings.MAX_CONCURRENT_PER_USER:
                text = get_text("too_many_downloads", lang, n=active)
            elif total_active >= settings.MAX_GLOBAL_CONCURRENT:
                text = get_text("server_busy", lang)
            else:
                text = get_text("too_many_downloads", lang, n=active)
            await _safe_edit(status_msg, text)
            return

        await track_user(user_id)

        # Get cookie file if user has one
        cookie_path = await get_user_cookies_path(user_id)

        # Progress callback (throttled)
        last_edit = [0.0]

        async def progress_cb(prog: DownloadProgress) -> None:
            now = time.monotonic()
            if prog.status == "retrying" or (now - last_edit[0] >= _PROGRESS_INTERVAL):
                last_edit[0] = now
                if prog.status == "retrying":
                    text = get_text(
                        "retrying", lang,
                        secs=prog.eta,
                        n=prog.speed.split("/")[0].split()[-1] if "/" in prog.speed else "?",
                        max=10,
                    )
                else:
                    text = get_text(
                        "downloading", lang,
                        percent=prog.percent,
                        bar=prog.bar,
                        speed=prog.speed,
                        eta=prog.eta,
                    )
                await _safe_edit(status_msg, text)

        downloader = Downloader(
            quality=quality,
            cookie_file=cookie_path,
            progress_cb=progress_cb,
        )

        result: DownloadResult = await downloader.download(url)

        if not result.success:
            await increment_stat("errors")
            await _safe_edit(
                status_msg,
                get_text("download_failed", lang, error=_truncate(result.error, 200)),
            )
            logger.warning("Download failed for user %s, url=%s: %s", user_id, url, result.error)
            return

        await increment_stat("downloads")

        # Handle playlist
        paths = result.playlist_paths or ([result.file_path] if result.file_path else [])
        if not paths:
            await _safe_edit(status_msg, get_text("download_failed", lang, error="No file produced"))
            return

        await _safe_edit(status_msg, get_text("download_done", lang))

        for file_path in paths:
            await _send_file(
                bot=bot,
                user_id=user_id,
                file_path=file_path,
                title=result.title,
                url=url,
                is_audio=result.is_audio,
                lang=lang,
                status_msg=status_msg,
            )

        # Cleanup the whole temp directory
        if paths:
            _safe_rmtree(os.path.dirname(paths[0]))

        # Clean up cookie temp file
        if cookie_path and cookie_path.startswith("/tmp/"):
            _safe_remove(cookie_path)


# ─── File sending ─────────────────────────────────────────────────────────────

async def _send_file(
    bot,
    user_id: int,
    file_path: str,
    title: str,
    url: str,
    is_audio: bool,
    lang: str,
    status_msg: Message,
) -> None:
    """Send file to user, compressing or uploading externally if needed."""
    if not os.path.exists(file_path):
        await _safe_edit(status_msg, get_text("download_failed", lang, error="File missing"))
        return

    file_size = os.path.getsize(file_path)
    caption = get_text("caption", lang, title=title, url=url, bot=settings.BOT_USERNAME)
    chat_id = status_msg.chat.id

    # Within Telegram limit — send directly
    if file_size <= settings.MAX_FILE_SIZE_BYTES:
        await _telegram_send(bot, chat_id, file_path, is_audio, caption)
        return

    # Over limit: try compression first
    size_human = _human_size(file_size)
    await _safe_edit(status_msg, get_text("file_too_large", lang, size=size_human))

    try:
        await _safe_edit(status_msg, get_text("compressing", lang))
        if is_audio:
            compressed = await extract_audio(file_path)
        else:
            compressed = await compress_video(file_path, settings.MAX_FILE_SIZE_BYTES)

        compressed_size = os.path.getsize(compressed)
        if compressed_size <= settings.MAX_FILE_SIZE_BYTES:
            await _telegram_send(bot, chat_id, compressed, is_audio, caption)
            if compressed != file_path:
                _safe_remove(compressed)
            return
        _safe_remove(compressed)

    except Exception as e:
        logger.warning("Compression failed: %s", e)

    # Compression failed/not enough: upload to external host
    await _safe_edit(status_msg, get_text("compress_failed", lang))
    try:
        ext_url = await upload_file(file_path)
        if ext_url:
            await bot.send_message(
                chat_id,
                get_text("external_link", lang, url=ext_url),
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
            return
    except Exception as e:
        logger.error("External upload failed: %s", e)

    await _safe_edit(
        status_msg,
        get_text("download_failed", lang, error=f"File too large ({size_human}) and could not be compressed or uploaded"),
    )


async def _telegram_send(bot, chat_id: int, file_path: str, is_audio: bool, caption: str) -> None:
    """Send file to Telegram chat."""
    f = FSInputFile(file_path)
    try:
        if is_audio or file_path.endswith(".mp3"):
            await bot.send_audio(chat_id, f, caption=caption, parse_mode="HTML")
        else:
            await bot.send_video(
                chat_id, f,
                caption=caption,
                parse_mode="HTML",
                supports_streaming=True,
            )
    except TelegramBadRequest:
        # Fallback to document
        await bot.send_document(chat_id, FSInputFile(file_path), caption=caption, parse_mode="HTML")


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_title(url: str, user_id: int) -> str:
    """Fetch video title without downloading."""
    cookie_path = None
    try:
        cookie_path = await get_user_cookies_path(user_id)
        dl = Downloader(quality="best", cookie_file=cookie_path)
        info = await asyncio.wait_for(dl.get_info(url), timeout=15)
        if info:
            return info.get("title") or info.get("id") or "Video"
    except (asyncio.TimeoutError, Exception) as e:
        logger.debug("get_title failed for %s: %s", url, e)
    finally:
        if cookie_path and cookie_path.startswith("/tmp/"):
            _safe_remove(cookie_path)
    return "Video"


async def _safe_edit(msg: Message, text: str) -> None:
    try:
        await msg.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)
    except TelegramBadRequest:
        pass
    except Exception as e:
        logger.debug("edit_text failed: %s", e)


def _safe_remove(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


def _safe_rmtree(path: str) -> None:
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
    except Exception:
        pass


def _truncate(text: str, max_len: int) -> str:
    return text[:max_len] + "…" if len(text) > max_len else text


def _human_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size} B"
