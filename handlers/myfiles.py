"""
/myfiles handler — list and re-send user-uploaded files.
"""
from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message

from keyboards import file_action_keyboard
from utils.i18n import get_text
from utils.redis_client import (
    delete_user_file,
    get_user_file,
    get_user_files,
    get_user_lang,
)

logger = logging.getLogger(__name__)
router = Router(name="myfiles")


@router.message(Command("myfiles"))
async def cmd_myfiles(message: Message) -> None:
    lang = await get_user_lang(message.from_user.id)
    files = await get_user_files(message.from_user.id)

    if not files:
        await message.answer(get_text("myfiles_empty", lang))
        return

    await message.answer(get_text("myfiles_header", lang), parse_mode="HTML")

    for i, (file_key, meta) in enumerate(files.items(), 1):
        name = meta.get("name", "unknown")
        size = _human_size(meta.get("size", 0))
        ts = meta.get("saved_at", 0)
        date = datetime.fromtimestamp(ts).strftime("%d.%m %H:%M") if ts else "—"

        text = get_text("myfiles_item", lang, n=i, name=name, size=size, date=date)
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=file_action_keyboard(file_key),
        )


# ─── Re-send callback ─────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith("file:resend:"))
async def cb_resend_file(call: CallbackQuery) -> None:
    lang = await get_user_lang(call.from_user.id)
    file_key = call.data.split("file:resend:", 1)[1]

    meta = await get_user_file(call.from_user.id, file_key)
    if not meta:
        await call.answer(get_text("file_not_found", lang), show_alert=True)
        return

    file_path = meta.get("path")
    tg_file_id = meta.get("file_id")

    try:
        if tg_file_id:
            # Re-send using Telegram file_id (most reliable)
            media_type = meta.get("type", "document")
            if media_type == "video":
                await call.message.answer_video(tg_file_id)
            elif media_type == "audio":
                await call.message.answer_audio(tg_file_id)
            else:
                await call.message.answer_document(tg_file_id)
        elif file_path:
            import os
            if not os.path.exists(file_path):
                await call.answer(get_text("file_not_found", lang), show_alert=True)
                return
            f = FSInputFile(file_path)
            await call.message.answer_document(f)
        else:
            await call.answer(get_text("file_not_found", lang), show_alert=True)
            return

        await call.answer(get_text("file_resent", lang))

    except Exception as e:
        logger.error("Re-send failed: %s", e)
        await call.answer(get_text("file_not_found", lang), show_alert=True)


# ─── Delete callback ──────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith("file:delete:"))
async def cb_delete_file(call: CallbackQuery) -> None:
    lang = await get_user_lang(call.from_user.id)
    file_key = call.data.split("file:delete:", 1)[1]

    deleted = await delete_user_file(call.from_user.id, file_key)
    if deleted:
        await call.message.edit_text(get_text("file_deleted", lang))
    else:
        await call.answer(get_text("file_not_found", lang), show_alert=True)


# ─── Helper ───────────────────────────────────────────────────────────────────

def _human_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size} B"
