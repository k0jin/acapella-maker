"""YouTube audio download functionality."""

import re
from pathlib import Path

import yt_dlp

from acapella_maker.exceptions import YouTubeDownloadError

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


def download_audio(url: str, output_dir: Path) -> Path:
    """Download audio from a YouTube URL.

    Args:
        url: YouTube URL to download from.
        output_dir: Directory to save the audio file.

    Returns:
        Path to the downloaded audio file.

    Raises:
        YouTubeDownloadError: If download fails.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

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
    }

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
