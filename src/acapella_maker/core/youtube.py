"""YouTube audio download functionality."""

import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Generator, Optional

import yt_dlp

from acapella_maker.exceptions import YouTubeDownloadError


def _get_ffmpeg_location() -> Optional[str]:
    """Find FFmpeg binary location.

    Checks in order:
    1. PyInstaller bundle directory (for standalone app)
    2. Project's ffmpeg_bin directory (for development)
    3. System PATH

    Returns:
        Path to directory containing ffmpeg, or None if not found.
    """
    # Check PyInstaller bundle directory
    if getattr(sys, "frozen", False):
        bundle_dir = Path(sys._MEIPASS)
        ffmpeg_path = bundle_dir / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
        if ffmpeg_path.exists():
            return str(bundle_dir)

    # Check project ffmpeg_bin directory (development)
    # Walk up from this file to find project root
    current = Path(__file__).resolve()
    for parent in current.parents:
        ffmpeg_bin = parent / "ffmpeg_bin"
        if ffmpeg_bin.exists():
            ffmpeg_path = ffmpeg_bin / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
            if ffmpeg_path.exists():
                return str(ffmpeg_bin)

    # Check system PATH
    if shutil.which("ffmpeg"):
        return None  # yt-dlp will find it automatically

    return None

YOUTUBE_PATTERNS = [
    r"^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+",
    r"^https?://(?:www\.)?youtube\.com/shorts/[\w-]+",
    r"^https?://youtu\.be/[\w-]+",
    r"^https?://(?:www\.)?youtube\.com/embed/[\w-]+",
    r"^https?://music\.youtube\.com/watch\?v=[\w-]+",
]


def is_youtube_url(url: str) -> bool:
    """Check if a string is a YouTube URL.

    Args:
        url: String to check.

    Returns:
        True if the string matches a YouTube URL pattern.
    """
    return any(re.match(pattern, url) for pattern in YOUTUBE_PATTERNS)


def download_audio(
    url: str,
    output_dir: Path,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> Path:
    """Download audio from a YouTube URL.

    Args:
        url: YouTube URL to download from.
        output_dir: Directory to save the audio file.
        progress_callback: Optional callback for progress updates (0-100).

    Returns:
        Path to the downloaded audio file.

    Raises:
        YouTubeDownloadError: If download fails.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    def _progress_hook(d: dict) -> None:
        if progress_callback and d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                # Download phase = 70% of total progress
                progress_callback((downloaded / total) * 70)
        elif progress_callback and d["status"] == "finished":
            progress_callback(70)

    def _postprocessor_hook(d: dict) -> None:
        if progress_callback and d["status"] == "finished":
            progress_callback(100)

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "progress_hooks": [_progress_hook],
        "postprocessor_hooks": [_postprocessor_hook],
    }

    # Use bundled FFmpeg if available
    ffmpeg_location = _get_ffmpeg_location()
    if ffmpeg_location:
        ydl_opts["ffmpeg_location"] = ffmpeg_location

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise YouTubeDownloadError(f"Failed to extract info from: {url}")

            title = info.get("title", "audio")
            title = yt_dlp.utils.sanitize_filename(title, restricted=True)
            output_path = output_dir / f"{title}.wav"

            if not output_path.exists():
                wav_files = list(output_dir.glob("*.wav"))
                if wav_files:
                    output_path = wav_files[0]
                else:
                    all_files = list(output_dir.iterdir())
                    files_found = [f.name for f in all_files] if all_files else ["(none)"]
                    raise YouTubeDownloadError(
                        f"Downloaded file not found at expected path: {output_path}. "
                        f"Files in directory: {', '.join(files_found)}"
                    )

            return output_path

    except yt_dlp.utils.DownloadError as e:
        raise YouTubeDownloadError(f"Failed to download from YouTube: {e}") from e
    except Exception as e:
        if isinstance(e, YouTubeDownloadError):
            raise
        raise YouTubeDownloadError(f"Unexpected error during download: {e}") from e


@contextmanager
def youtube_audio(
    url: str,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> Generator[Path, None, None]:
    """Download YouTube audio, yield path, auto-cleanup.

    Args:
        url: YouTube URL to download from.
        progress_callback: Optional callback for progress updates (0-100).

    Yields:
        Path to the downloaded audio file.

    Raises:
        YouTubeDownloadError: If download fails.
    """
    temp_dir = tempfile.mkdtemp(prefix="acapella_maker_")
    try:
        yield download_audio(url, Path(temp_dir), progress_callback)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
