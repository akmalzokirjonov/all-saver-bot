"""
Upload large files to temporary hosting services.

Priority order:
  1. catbox.moe  (3-day retention, no account needed, 200 MB limit)
  2. file.io     (1 download, 14-day retention)
  3. transfer.sh (14-day retention)
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=300)  # 5 min upload timeout


async def upload_file(file_path: str) -> Optional[str]:
    """
    Upload *file_path* to first available temp host.
    Returns public download URL or None if all fail.
    """
    for uploader in (_upload_catbox, _upload_fileio, _upload_transfersh):
        try:
            url = await uploader(file_path)
            if url:
                logger.info("Uploaded %s → %s", file_path, url)
                return url
        except Exception as e:
            logger.warning("Upload attempt failed (%s): %s", uploader.__name__, e)
    return None


# ─── Backends ─────────────────────────────────────────────────────────────────

async def _upload_catbox(file_path: str) -> Optional[str]:
    """Upload to catbox.moe – up to 200 MB, no expiry."""
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        with open(file_path, "rb") as f:
            data = aiohttp.FormData()
            data.add_field("reqtype", "fileupload")
            data.add_field(
                "fileToUpload",
                f,
                filename=os.path.basename(file_path),
            )
            async with session.post(
                "https://catbox.moe/user/api.php", data=data
            ) as resp:
                text = await resp.text()
                if resp.status == 200 and text.startswith("https://"):
                    return text.strip()
    return None


async def _upload_fileio(file_path: str) -> Optional[str]:
    """Upload to file.io – single download, 14 days."""
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        with open(file_path, "rb") as f:
            data = aiohttp.FormData()
            data.add_field(
                "file",
                f,
                filename=os.path.basename(file_path),
            )
            async with session.post(
                "https://file.io/?expires=14d", data=data
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("link")
    return None


async def _upload_transfersh(file_path: str) -> Optional[str]:
    """Upload to transfer.sh – 14 days."""
    filename = os.path.basename(file_path)
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        with open(file_path, "rb") as f:
            async with session.put(
                f"https://transfer.sh/{filename}", data=f
            ) as resp:
                if resp.status == 200:
                    return (await resp.text()).strip()
    return None
