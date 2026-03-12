"""
Admin-only commands: /stats
"""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from download_queue import get_total_active
from utils.i18n import get_text
from utils.redis_client import get_stats, get_user_lang

logger = logging.getLogger(__name__)
router = Router(name="admin")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    user_id = user.id
    lang = await get_user_lang(user_id)

    if user_id not in settings.ADMIN_IDS:
        await message.answer(get_text("not_admin", lang))
        return

    stats = await get_stats()
    active = await get_total_active()

    await message.answer(
        get_text(
            "stats",
            lang,
            downloads=stats.get("downloads", 0),
            errors=stats.get("errors", 0),
            users=stats.get("users", 0),
            queue=0,
            active=active,
        ),
        parse_mode="HTML",
    )
