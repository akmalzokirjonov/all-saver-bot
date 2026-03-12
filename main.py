"""
Bot entry point.

Startup order:
  1. Logging setup
  2. Redis connection
  3. Register routers & middlewares
  4. Start polling
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from config import settings
from handlers import admin, cookies, download, myfiles, start, upload
from middlewares.throttling import ThrottlingMiddleware
from utils.redis_client import close_redis, setup_redis


# ─── Logging ──────────────────────────────────────────────────────────────────

def _setup_logging() -> None:
    os.makedirs(os.path.dirname(settings.LOG_FILE) or "logs", exist_ok=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    # Also configure stdlib logging to file
    file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL.upper())
    root.addHandler(file_handler)
    root.addHandler(logging.StreamHandler(sys.stdout))


# ─── Bot setup ────────────────────────────────────────────────────────────────

async def main() -> None:
    _setup_logging()
    log = structlog.get_logger()
    log.info("Starting bot", username=settings.BOT_USERNAME)

    # Connect to Redis
    redis_client = await setup_redis()

    # FSM storage backed by Redis
    storage = RedisStorage(redis=redis_client)

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=storage)

    # ── Middlewares ────────────────────────────────────────────────────────
    dp.message.middleware(ThrottlingMiddleware())

    # ── Routers (order matters — more specific first) ──────────────────────
    dp.include_router(start.router)
    dp.include_router(cookies.router)    # must be before upload (handles documents)
    dp.include_router(download.router)
    dp.include_router(upload.router)
    dp.include_router(myfiles.router)
    dp.include_router(admin.router)

    # ── Lifecycle hooks ────────────────────────────────────────────────────
    async def on_startup() -> None:
        me = await bot.get_me()
        log.info("Bot ready", id=me.id, username=me.username)
        # Set bot commands
        from aiogram.types import BotCommand
        await bot.set_my_commands([
            BotCommand(command="start",         description="Start the bot"),
            BotCommand(command="help",          description="Show help"),
            BotCommand(command="language",      description="Change language"),
            BotCommand(command="cookies",       description="Set cookies for private content"),
            BotCommand(command="deletecookies", description="Remove stored cookies"),
            BotCommand(command="myfiles",       description="View your uploaded files"),
            BotCommand(command="stats",         description="Bot statistics (admin only)"),
        ])

    async def on_shutdown() -> None:
        log.info("Shutting down…")
        await close_redis()
        await bot.session.close()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # ── Start polling ──────────────────────────────────────────────────────
    log.info("Starting polling…")
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
