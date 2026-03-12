"""Centralised configuration via pydantic-settings."""
from __future__ import annotations

import os
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Bot ─────────────────────────────────────────────────────────────────
    BOT_TOKEN: str
    BOT_USERNAME: str = "TelebramBot"

    # ── Admins ───────────────────────────────────────────────────────────────
    ADMIN_IDS: List[int] = []

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v or []

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Storage ──────────────────────────────────────────────────────────────
    DOWNLOAD_DIR: str = "/tmp/tg_downloads"

    # ── Limits ───────────────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 50
    MAX_FILE_SIZE_BYTES: int = 0          # computed below
    MAX_CONCURRENT_PER_USER: int = 2
    MAX_GLOBAL_CONCURRENT: int = 20
    MAX_PLAYLIST_VIDEOS: int = 5

    # ── Active download tracking ─────────────────────────────────────────────
    ACTIVE_DOWNLOAD_TTL_SECONDS: int = 3600

    # ── Expiry ───────────────────────────────────────────────────────────────
    COOKIE_EXPIRE_DAYS: int = 30
    FILE_EXPIRE_HOURS: int = 24

    # ── Defaults ─────────────────────────────────────────────────────────────
    DEFAULT_LANG: str = "en"

    # ── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/bot.log"

    def model_post_init(self, __context) -> None:
        self.MAX_FILE_SIZE_BYTES = self.MAX_FILE_SIZE_MB * 1024 * 1024
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.LOG_FILE) or "logs", exist_ok=True)


settings = Settings()
