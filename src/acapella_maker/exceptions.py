"""Custom exceptions for Acapella Maker."""


class AcapellaMakerError(Exception):
    """Base exception for Acapella Maker."""

    pass


class AudioLoadError(AcapellaMakerError):
    """Failed to load audio file."""

    pass


class AudioSaveError(AcapellaMakerError):
    """Failed to save audio file."""

    pass


class BPMDetectionError(AcapellaMakerError):
    """Failed to detect BPM."""

    pass


class VocalExtractionError(AcapellaMakerError):
    """Failed to extract vocals."""

    pass


class SilenceTrimmingError(AcapellaMakerError):
    """Failed to trim silence."""

    pass
