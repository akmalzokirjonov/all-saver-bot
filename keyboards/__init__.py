"""Inline keyboards for the bot."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ── Quality Selection ─────────────────────────────────────────────────────────

QUALITY_OPTIONS = [
    ("🏆 Best Quality", "q:best"),
    ("📺 1080p",        "q:1080"),
    ("📺 720p",         "q:720"),
    ("📺 480p",         "q:480"),
    ("🎵 Audio MP3 320kbps", "q:audio"),
    ("📦 Low Size (<20MB)", "q:low"),
]


def quality_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, callback in QUALITY_OPTIONS:
        builder.button(text=label, callback_data=callback)
    builder.button(text="❌ Cancel", callback_data="q:cancel")
    builder.adjust(2)  # 2 buttons per row
    return builder.as_markup()


# ── Language Selection ────────────────────────────────────────────────────────

LANG_OPTIONS = [
    ("🇬🇧 English",  "lang:en"),
    ("🇺🇿 O'zbekcha", "lang:uz"),
    ("🇷🇺 Русский",  "lang:ru"),
]


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, callback in LANG_OPTIONS:
        builder.button(text=label, callback_data=callback)
    builder.adjust(1)
    return builder.as_markup()


# ── File Actions ──────────────────────────────────────────────────────────────

def file_action_keyboard(file_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Re-send", callback_data=f"file:resend:{file_key}")
    builder.button(text="🗑️ Delete",  callback_data=f"file:delete:{file_key}")
    builder.adjust(2)
    return builder.as_markup()


# ── Confirmation ──────────────────────────────────────────────────────────────

def confirm_keyboard(action: str, payload: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yes", callback_data=f"{action}:yes:{payload}")
    builder.button(text="❌ No",  callback_data=f"{action}:no:{payload}")
    builder.adjust(2)
    return builder.as_markup()
