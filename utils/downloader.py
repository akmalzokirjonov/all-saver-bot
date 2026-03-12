"""
Core download engine using yt-dlp with:
  - Per-quality format selection
  - Real-time progress callbacks
  - Tenacity retry with exponential backoff
  - Per-user cookie support
  - Resume-capable downloads
  - Playlist support (limited to MAX_PLAYLIST_VIDEOS)
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

import yt_dlp
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings

logger = logging.getLogger(__name__)

# ─── Quality presets ──────────────────────────────────────────────────────────

QUALITY_FORMATS: dict[str, str] = {
    "best":  "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
    "1080":  "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720":   "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480":   "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]",
    "audio": "bestaudio[ext=m4a]/bestaudio/best",
    "low":   "worstvideo+worstaudio/worst/best",
}

# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class DownloadProgress:
    status: str = "idle"         # idle / downloading / finished / error
    percent: float = 0.0
    speed: str = "—"
    eta: str = "—"
    filename: str = ""
    total_bytes: int = 0
    downloaded_bytes: int = 0

    @property
    def bar(self) -> str:
        filled = int(self.percent / 10)
        return "█" * filled + "░" * (10 - filled)


@dataclass
class DownloadResult:
    success: bool
    file_path: Optional[str] = None
    title: str = ""
    url: str = ""
    is_audio: bool = False
    playlist_paths: list[str] = field(default_factory=list)
    error: str = ""


# ─── Exceptions ───────────────────────────────────────────────────────────────

class TemporaryDownloadError(Exception):
    """Retriable download error (network, HTTP 5xx, etc.)."""

class PermanentDownloadError(Exception):
    """Non-retriable error (private content, unsupported URL, etc.)."""


_RETRIABLE_PATTERNS = [
    "connection reset", "timed out", "temporarily unavailable",
    "http error 5", "read timeout", "fragment", "unable to download",
    "too many requests", "429", "503", "502", "504",
    "network", "ssl", "certificate",
]

_PERMANENT_PATTERNS = [
    "private video", "login required", "not available",
    "removed", "404", "no video", "unsupported url",
    "copyright", "age-restricted",
]


def _classify_error(exc: Exception) -> None:
    """Re-raise as Temporary or Permanent based on message."""
    msg = str(exc).lower()
    if any(p in msg for p in _PERMANENT_PATTERNS):
        raise PermanentDownloadError(str(exc)) from exc
    raise TemporaryDownloadError(str(exc)) from exc


# ─── Retry callback ──────────────────────────────────────────────────────────

ProgressCallback = Callable[[DownloadProgress], Coroutine[Any, Any, None]]


def _make_retry_notifier(
    progress_cb: Optional[ProgressCallback],
    loop: asyncio.AbstractEventLoop,
    max_attempts: int,
) -> Callable[[RetryCallState], None]:
    """Return a tenacity before_sleep callback that notifies the user."""
    def _notify(retry_state: RetryCallState) -> None:
        if progress_cb is None:
            return
        wait = retry_state.next_action.sleep  # type: ignore[union-attr]
        n = retry_state.attempt_number
        prog = DownloadProgress(
            status="retrying",
            percent=0,
            speed=f"Retry {n}/{max_attempts}",
            eta=f"{int(wait)}s",
        )
        asyncio.run_coroutine_threadsafe(progress_cb(prog), loop)
    return _notify


# ─── Core downloader ─────────────────────────────────────────────────────────

class Downloader:
    def __init__(
        self,
        quality: str = "best",
        cookie_file: Optional[str] = None,
        progress_cb: Optional[ProgressCallback] = None,
    ):
        self.quality = quality
        self.cookie_file = cookie_file
        self.progress_cb = progress_cb
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._current_progress = DownloadProgress()

    # ── Public API ────────────────────────────────────────────────────────────

    async def download(self, url: str) -> DownloadResult:
        """Download URL and return DownloadResult."""
        self._loop = asyncio.get_running_loop()

        is_audio = self.quality == "audio"
        out_dir = self._make_temp_dir()

        try:
            result = await self._download_with_retry(url, out_dir, is_audio)
            if not result.success:
                self._safe_rmtree(out_dir)
            return result
        except PermanentDownloadError as e:
            self._safe_rmtree(out_dir)
            return DownloadResult(success=False, url=url, error=str(e))
        except Exception as e:
            logger.error("Download failed for %s: %s", url, e)
            self._safe_rmtree(out_dir)
            return DownloadResult(success=False, url=url, error=str(e))

    @staticmethod
    def _safe_rmtree(path: str) -> None:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
        except Exception:
            pass

    async def get_info(self, url: str) -> Optional[dict]:
        """Fetch metadata without downloading."""
        ydl_opts = self._base_opts(out_dir=None, is_audio=False)
        ydl_opts["skip_download"] = True
        try:
            info = await asyncio.to_thread(self._run_ydl_info, url, ydl_opts)
            return info
        except Exception as e:
            logger.warning("get_info failed for %s: %s", url, e)
            return None

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _download_with_retry(
        self, url: str, out_dir: str, is_audio: bool
    ) -> DownloadResult:
        """Wrapped download with tenacity retries."""
        max_attempts = 10
        loop = self._loop

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=3, max=60),
            retry=retry_if_exception_type(TemporaryDownloadError),
            before_sleep=_make_retry_notifier(self.progress_cb, loop, max_attempts),
            reraise=True,
        )
        def _do_download() -> DownloadResult:
            ydl_opts = self._build_opts(out_dir, is_audio)
            try:
                title, paths = self._run_ydl(url, ydl_opts)
            except yt_dlp.utils.DownloadError as e:
                _classify_error(e)
            except Exception as e:
                _classify_error(e)

            if not paths:
                raise TemporaryDownloadError("No output file produced")

            if len(paths) == 1:
                return DownloadResult(
                    success=True,
                    file_path=paths[0],
                    title=title,
                    url=url,
                    is_audio=is_audio,
                )
            return DownloadResult(
                success=True,
                file_path=paths[0],
                title=title,
                url=url,
                is_audio=is_audio,
                playlist_paths=paths,
            )

        return await asyncio.to_thread(_do_download)

    def _run_ydl(self, url: str, opts: dict) -> tuple[str, list[str]]:
        """Run yt-dlp synchronously. Returns (title, [file_paths])."""
        title = "Video"

        opts["progress_hooks"] = opts.get("progress_hooks", []) + [
            self._make_sync_progress_hook()
        ]

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                title = info.get("title") or info.get("id") or "Video"

        # Scan out_dir for any valid completed files
        downloaded_files: list[str] = []
        out_dir = opts.get("paths", {}).get("home", "")
        if out_dir and os.path.isdir(out_dir):
            for f in sorted(os.listdir(out_dir)):
                # Ignore yt-dlp temporary files
                if f.endswith(".part") or f.endswith(".ytdl"):
                    continue
                fp = os.path.join(out_dir, f)
                if os.path.isfile(fp):
                    downloaded_files.append(fp)

        return title, downloaded_files

    def _run_ydl_info(self, url: str, opts: dict) -> Optional[dict]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _make_sync_progress_hook(self) -> Callable[[dict], None]:
        """Build a yt-dlp progress hook that reports to async callback."""
        def _hook(d: dict) -> None:
            if d["status"] not in ("downloading", "finished"):
                return

            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            percent = (downloaded / total * 100) if total else 0
            speed_raw = d.get("speed") or 0
            speed_str = _human_speed(speed_raw)
            eta_raw = d.get("eta") or 0
            eta_str = _human_eta(eta_raw)
            filename = os.path.basename(d.get("filename", ""))

            prog = DownloadProgress(
                status=d["status"],
                percent=round(percent, 1),
                speed=speed_str,
                eta=eta_str,
                filename=filename,
                total_bytes=total,
                downloaded_bytes=downloaded,
            )
            self._current_progress = prog

            if self.progress_cb and self._loop:
                asyncio.run_coroutine_threadsafe(
                    self.progress_cb(prog), self._loop
                )

        return _hook

    def _build_opts(self, out_dir: str, is_audio: bool) -> dict:
        opts = self._base_opts(out_dir, is_audio)

        fmt = QUALITY_FORMATS.get(self.quality, QUALITY_FORMATS["best"])
        opts["format"] = fmt

        if is_audio:
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ]

        return opts

    def _base_opts(self, out_dir: Optional[str], is_audio: bool) -> dict:
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": False,
            "ignoreerrors": False,
            "noplaylist": False,            # allow playlists (limited below)
            "playlistend": settings.MAX_PLAYLIST_VIDEOS,
            "merge_output_format": "mp4",
            "writethumbnail": False,
            "writeinfojson": False,
            "socket_timeout": 30,
            "retries": 3,                  # yt-dlp internal retries (tenacity wraps outer)
            "fragment_retries": 5,
            "continuedl": True,            # resume interrupted downloads
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            },
        }

        if out_dir:
            opts["paths"] = {"home": out_dir}
            opts["outtmpl"] = os.path.join(out_dir, "%(title).80s.%(ext)s")

        if self.cookie_file and os.path.isfile(self.cookie_file):
            opts["cookiefile"] = self.cookie_file

        # Platform-specific tweaks
        opts.update(_platform_opts())

        return opts

    @staticmethod
    def _make_temp_dir() -> str:
        tmp = os.path.join(settings.DOWNLOAD_DIR, f"dl_{int(time.time() * 1000)}")
        os.makedirs(tmp, exist_ok=True)
        return tmp


# ─── Platform-specific options ───────────────────────────────────────────────

def _platform_opts() -> dict:
    """Extra yt-dlp options that improve compatibility across platforms."""
    return {
        # TikTok: no watermark
        "extractor_args": {
            "tiktok": {"api_hostname": ["api22-normal-c-useast2a.tiktokv.com"]},
        },
        # Instagram: use mobile API
        "compat_opts": set(),
    }


# ─── URL validation ──────────────────────────────────────────────────────────

_URL_RE = re.compile(
    r"(https?://"
    r"(?:www\.)?"
    r"(?:"
    r"instagram\.com|tiktok\.com|youtube\.com|youtu\.be|"
    r"twitter\.com|x\.com|facebook\.com|fb\.watch|"
    r"vimeo\.com|soundcloud\.com|pinterest\.com|"
    r"reddit\.com|redd\.it|"
    r"[\w\-\.]+\.\w{2,}"
    r")"
    r"/\S+)",
    re.IGNORECASE,
)


def extract_url(text: str) -> Optional[str]:
    """Extract first URL from text."""
    m = _URL_RE.search(text)
    return m.group(1) if m else None


def is_supported_url(url: str) -> bool:
    """Quick check using yt-dlp extractor list."""
    try:
        extractors = yt_dlp.extractor.gen_extractors()
        for e in extractors:
            if e.suitable(url):
                return True
        return False
    except Exception:
        return True  # optimistic: let yt-dlp try


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _human_speed(bps: float) -> str:
    if not bps:
        return "—"
    if bps >= 1024 * 1024:
        return f"{bps / 1024 / 1024:.1f} MB/s"
    if bps >= 1024:
        return f"{bps / 1024:.0f} KB/s"
    return f"{bps:.0f} B/s"


def _human_eta(secs: float) -> str:
    if not secs:
        return "—"
    m, s = divmod(int(secs), 60)
    if m:
        return f"{m}m {s}s"
    return f"{s}s"
