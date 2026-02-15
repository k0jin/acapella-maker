"""Custom exceptions for Acapella."""


class AcapellaError(Exception):
    """Base exception for Acapella."""

    pass


class AudioLoadError(AcapellaError):
    """Failed to load audio file."""

    pass


class AudioSaveError(AcapellaError):
    """Failed to save audio file."""

    pass


class BPMDetectionError(AcapellaError):
    """Failed to detect BPM."""

    pass


class VocalExtractionError(AcapellaError):
    """Failed to extract vocals."""

    pass


class SilenceTrimmingError(AcapellaError):
    """Failed to trim silence."""

    pass


class YouTubeDownloadError(AcapellaError):
    """Failed to download from YouTube."""

    pass
