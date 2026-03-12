"""
Video/audio compression via ffmpeg.

Strategy:
  1. Target resolution 720p (or 480p if still too large)
  2. Use CRF-based encoding for size control
  3. For audio-only: re-encode to mp3 320 kbps
"""
from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── Targets ──────────────────────────────────────────────────────────────────
_MAX_BYTES = 50 * 1024 * 1024   # 50 MB Telegram limit
_SAFETY_FACTOR = 0.95           # leave 5% headroom


async def compress_video(
    input_path: str,
    max_bytes: int = _MAX_BYTES,
    target_height: int = 720,
) -> str:
    """
    Compress *input_path* to fit within *max_bytes*.

    Returns path to compressed file (may be same as input if already small).
    Raises RuntimeError if compression still exceeds limit.
    """
    input_size = await asyncio.to_thread(os.path.getsize, input_path)
    if input_size <= max_bytes:
        return input_path

    output_path = _make_output_path(input_path, suffix="_compressed.mp4")

    # First pass: try 720p
    result = await _run_ffmpeg_compress(input_path, output_path, target_height, max_bytes)
    out1_exists = await asyncio.to_thread(os.path.exists, output_path)
    if result and out1_exists:
        out1_size = await asyncio.to_thread(os.path.getsize, output_path)
        if out1_size <= max_bytes:
            logger.info("Compressed %s → %s (720p)", input_path, output_path)
            return output_path

    # Second pass: try 480p
    output_path2 = _make_output_path(input_path, suffix="_compressed_480p.mp4")
    result = await _run_ffmpeg_compress(input_path, output_path2, 480, max_bytes)
    out2_exists = await asyncio.to_thread(os.path.exists, output_path2)
    if result and out2_exists:
        out2_size = await asyncio.to_thread(os.path.getsize, output_path2)
        if out2_size <= max_bytes:
            logger.info("Compressed %s → %s (480p)", input_path, output_path2)
            # clean up intermediate
            await asyncio.to_thread(_safe_remove, output_path)
            return output_path2

    await asyncio.to_thread(_safe_remove, output_path)
    await asyncio.to_thread(_safe_remove, output_path2)
    raise RuntimeError(f"Could not compress {input_path} below {max_bytes // 1024 // 1024} MB")


async def extract_audio(input_path: str, bitrate: str = "320k") -> str:
    """
    Extract audio from video file and encode as mp3.
    Returns path to .mp3 file.
    """
    output_path = _make_output_path(input_path, suffix="_audio.mp3")
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", bitrate,
        "-ar", "44100",
        output_path,
    ]
    ok = await _run_command(cmd)
    if not ok:
        raise RuntimeError(f"Audio extraction failed for {input_path}")
    return output_path


async def get_duration(path: str) -> float:
    """Return duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return float(stdout.strip())
    except Exception:
        return 0.0


# ─── Internal helpers ─────────────────────────────────────────────────────────

async def _run_ffmpeg_compress(
    input_path: str,
    output_path: str,
    target_height: int,
    max_bytes: int,
) -> bool:
    """
    Run ffmpeg to compress video to *target_height* with bitrate calculated
    to fit within *max_bytes*.
    """
    duration = await get_duration(input_path)
    if duration <= 0:
        duration = 60  # fallback

    # Target bitrate (kbps) = max_bytes * 8 / duration / 1000 * safety
    target_total_kbps = int(max_bytes * 8 / duration / 1000 * _SAFETY_FACTOR)
    
    audio_kbps = min(128, int(target_total_kbps * 0.3)) if target_total_kbps > 64 else 32
    video_kbps = target_total_kbps - audio_kbps
    
    if video_kbps < 50:
        logger.warning(f"Calculated video bitrate {video_kbps}k is too low for a {duration}s video. Failing compression.")
        return False

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        # scale to target height, keep aspect ratio
        "-vf", f"scale=-2:{target_height}",
        "-c:v", "libx264",
        "-b:v", f"{video_kbps}k",
        "-maxrate", f"{video_kbps}k",
        "-bufsize", f"{video_kbps * 2}k",
        "-c:a", "aac",
        "-b:a", f"{audio_kbps}k",
        "-movflags", "+faststart",
        "-preset", "fast",
        output_path,
    ]
    return await _run_command(cmd)


async def _run_command(cmd: list[str]) -> bool:
    """Run a subprocess command async. Returns True on success."""
    logger.debug("Running: %s", " ".join(cmd))
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning("ffmpeg error: %s", stderr.decode(errors="replace")[-500:])
            return False
        return True
    except FileNotFoundError:
        logger.error("ffmpeg not found in PATH")
        return False
    except Exception as e:
        logger.error("ffmpeg exception: %s", e)
        return False


def _make_output_path(input_path: str, suffix: str) -> str:
    p = Path(input_path)
    return str(p.parent / (p.stem + suffix))


def _safe_remove(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass
