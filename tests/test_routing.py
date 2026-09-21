"""Offline checks that catch catch-all handlers swallowing later commands."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch


class CommandRoutingTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        cls.env = patch.dict(os.environ, {
            "BOT_TOKEN": "123456789:TEST_TOKEN_FOR_OFFLINE_CHECKS_ONLY",
            "ADMIN_IDS": "123456",
            "DOWNLOAD_DIR": str(Path(cls.scratch.name) / "downloads"),
            "LOG_FILE": str(Path(cls.scratch.name) / "bot.log"),
        })
        cls.env.start()
        from aiogram import Dispatcher
        from handlers import admin, cookies, download, myfiles, start, upload
        cls.admin = admin
        cls.myfiles = myfiles
        cls.dp = Dispatcher()
        # The polling and webhook entry points register this same router order.
        cls.dp.include_routers(start.router, cookies.router, download.router,
                               upload.router, myfiles.router, admin.router)

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()
        cls.scratch.cleanup()

    async def send_command(self, command):
        from aiogram import Bot
        from aiogram.types import Update
        bot = Bot(token="123456789:TEST_TOKEN_FOR_OFFLINE_CHECKS_ONLY")
        update = Update.model_validate({
            "update_id": 1,
            "message": {
                "message_id": 1, "date": 0,
                "chat": {"id": 123456, "type": "private"},
                "from": {"id": 123456, "is_bot": False, "first_name": "Test"},
                "text": command,
                "entities": [{"type": "bot_command", "offset": 0, "length": len(command)}],
            },
        })
        try:
            await self.dp.feed_update(bot, update)
        finally:
            await bot.session.close()

    async def test_myfiles_reaches_its_handler(self):
        from aiogram.types import Message
        with patch.object(self.myfiles, "get_user_lang", AsyncMock(return_value="en")), \
             patch.object(self.myfiles, "get_user_files", AsyncMock(return_value={})) as files, \
             patch.object(Message, "answer", AsyncMock()) as answer:
            await self.send_command("/myfiles")
            files.assert_awaited_once_with(123456)
            answer.assert_awaited_once()

    async def test_stats_reaches_its_handler(self):
        from aiogram.types import Message
        with patch.object(self.admin, "get_user_lang", AsyncMock(return_value="en")), \
             patch.object(self.admin, "get_stats", AsyncMock(return_value={})) as stats, \
             patch.object(self.admin, "get_total_active", AsyncMock(return_value=0)), \
             patch.object(Message, "answer", AsyncMock()) as answer:
            await self.send_command("/stats")
            stats.assert_awaited_once()
            answer.assert_awaited_once()
