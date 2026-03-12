"""
/cookies FSM handler.
Accepts a Netscape-format .txt cookie file and stores it in Redis.
"""
from __future__ import annotations

import logging
import os
import tempfile

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Document, Message

from states import CookieState
from utils.i18n import get_text
from utils.redis_client import delete_user_cookies, get_user_lang, set_user_cookies

logger = logging.getLogger(__name__)
router = Router(name="cookies")

_NETSCAPE_HEADER = "# Netscape HTTP Cookie File"
_MAX_COOKIE_SIZE = 512 * 1024  # 512 KB


# ─── /cookies ────────────────────────────────────────────────────────────────

@router.message(Command("cookies"))
async def cmd_cookies(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    lang = await get_user_lang(message.from_user.id)
    await state.set_state(CookieState.waiting_file)
    await message.answer(
        get_text("cookies_prompt", lang),
        parse_mode="HTML",
        reply_markup=_cancel_keyboard(lang),
    )


@router.message(CookieState.waiting_file, F.document)
async def receive_cookie_file(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    lang = await get_user_lang(message.from_user.id)
    doc: Document = message.document

    # Basic validation
    if doc.file_size and doc.file_size > _MAX_COOKIE_SIZE:
        await message.answer(get_text("cookies_invalid", lang))
        return

    # Download to temp file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await message.bot.download(doc, destination=tmp_path)
        with open(tmp_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if not _is_netscape_cookies(content):
            await message.answer(get_text("cookies_invalid", lang))
            return

        await set_user_cookies(message.from_user.id, content)
        await state.clear()
        await message.answer(get_text("cookies_saved", lang), parse_mode="HTML")

    except Exception as e:
        logger.error("Cookie file processing failed: %s", e)
        await message.answer(get_text("cookies_invalid", lang))
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@router.message(CookieState.waiting_file)
async def cookie_wrong_input(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    lang = await get_user_lang(message.from_user.id)
    # If user sends cancel or other text
    if message.text and message.text.lower() in ("/cancel", "cancel"):
        await state.clear()
        await message.answer(get_text("cookies_cancel", lang))
        return
    await message.answer(get_text("cookies_prompt", lang), parse_mode="HTML")


# ─── /deletecookies ──────────────────────────────────────────────────────────

@router.message(Command("deletecookies"))
async def cmd_delete_cookies(message: Message) -> None:
    if not message.from_user:
        return
    lang = await get_user_lang(message.from_user.id)
    await delete_user_cookies(message.from_user.id)
    await message.answer(get_text("cookies_deleted", lang), parse_mode="HTML")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _is_netscape_cookies(content: str) -> bool:
    """Validate the cookie file starts with Netscape header or has tab-delimited lines."""
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if not lines:
        return False
    # Standard Netscape header
    if lines[0].startswith("# Netscape") or lines[0].startswith("# HTTP Cookie"):
        return True
    # Some tools omit the header but still produce valid format
    # Check if most data lines have 7 tab-separated fields
    data_lines = [l for l in lines if not l.startswith("#")]
    if data_lines:
        sample = data_lines[:5]
        valid = sum(1 for l in sample if len(l.split("\t")) == 7)
        return valid >= len(sample) // 2
    return False


def _cancel_keyboard(lang: str):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=get_text("cookies_cancel_btn", lang), callback_data="cookies:cancel")
    ]])


@router.callback_query(lambda c: c.data == "cookies:cancel")
async def cb_cancel_cookies(call: CallbackQuery, state: FSMContext) -> None:
    lang = await get_user_lang(call.from_user.id)
    await state.clear()
    await call.message.edit_text(get_text("cookies_cancel", lang))
    await call.answer()
