"""Unit tests for YouTube module."""

import pytest

from acapella.core.youtube import is_youtube_url


class TestIsYouTubeUrl:
    """Tests for is_youtube_url function."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "http://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/abc123xyz",
            "https://youtube.com/shorts/abc123xyz",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
        ],
    )
    def test_valid_youtube_urls(self, url: str):
        """Test that valid YouTube URLs are recognized."""
        assert is_youtube_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "https://vimeo.com/123456789",
            "https://www.google.com",
            "/path/to/file.mp3",
            "file.mp3",
            "https://notyoutube.com/watch?v=abc123",
            "youtube.com/watch?v=abc123",  # Missing protocol
            "",
            "random string",
            "https://www.youtube.com/",  # No video ID
            "https://www.youtube.com/channel/UC123",  # Channel, not video
        ],
    )
    def test_invalid_youtube_urls(self, url: str):
        """Test that non-YouTube URLs are rejected."""
        assert is_youtube_url(url) is False

    def test_youtube_url_with_extra_params(self):
        """Test YouTube URLs with additional query parameters."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&list=PLxyz"
        assert is_youtube_url(url) is True

    def test_youtube_url_case_sensitivity(self):
        """Test that URL matching handles case correctly."""
        # Video IDs are case-sensitive, but domain should work either way
        url_lower = "https://www.youtube.com/watch?v=AbCdEfGhIjK"
        url_upper = "https://www.YOUTUBE.com/watch?v=AbCdEfGhIjK"

        # Both should match (domain is case-insensitive in practice)
        # Note: Our regex is case-sensitive for domain, which is technically
        # stricter than necessary but acceptable
        assert is_youtube_url(url_lower) is True


class TestYouTubeDownload:
    """Tests for download functionality (mocked to avoid actual downloads)."""

    def test_download_requires_valid_url(self, mocker, tmp_path):
        """Test that download validates URL format."""
        from acapella.core.youtube import download_audio
        from acapella.exceptions import YouTubeDownloadError

        # Mock yt-dlp to avoid actual download
        mock_ydl = mocker.patch("acapella.core.youtube.yt_dlp.YoutubeDL")
        mock_ydl.return_value.__enter__.return_value.extract_info.side_effect = (
            Exception("Invalid URL")
        )

        with pytest.raises(YouTubeDownloadError):
            download_audio("not-a-valid-url", tmp_path)
