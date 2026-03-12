"""
/start, /help, /language handlers.
"""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import language_keyboard
from states import LanguageState
from utils.i18n import get_text
from utils.redis_client import get_user_lang, set_user_lang, has_user_lang

router = Router(name="start")


# ─── /start ──────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    name = message.from_user.full_name or "friend"
    
    if not await has_user_lang(user_id):
        await state.set_state(LanguageState.choosing)
        await message.answer(
            "🌐 Please choose your language / Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
            reply_markup=language_keyboard(),
        )
        return

    lang = await get_user_lang(user_id)
    await message.answer(
        get_text("start", lang, name=name),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


# ─── /help ───────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if not message.from_user:
        return
    lang = await get_user_lang(message.from_user.id)
    await message.answer(
        get_text("help", lang),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


# ─── /language ───────────────────────────────────────────────────────────────

@router.message(Command("language"))
async def cmd_language(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    lang = await get_user_lang(message.from_user.id)
    await state.set_state(LanguageState.choosing)
    await message.answer(
        get_text("language_prompt", lang),
        reply_markup=language_keyboard(),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("lang:"))
async def cb_language(call: CallbackQuery, state: FSMContext) -> None:
    chosen = call.data.split(":", 1)[1]
    user_id = call.from_user.id
    
    had_lang_before = await has_user_lang(user_id)
    await set_user_lang(user_id, chosen)
    await state.clear()
    
    await call.message.edit_text(
        get_text("language_set", chosen),
        parse_mode="HTML",
    )
    
    if not had_lang_before:
        name = call.from_user.full_name or "friend"
        await call.message.answer(
            get_text("start", chosen, name=name),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        
    await call.answer()
