"""Unit tests for exception classes."""

import pytest

from acapella_maker.exceptions import (
    AcapellaMakerError,
    AudioLoadError,
    AudioSaveError,
    BPMDetectionError,
    SilenceTrimmingError,
    VocalExtractionError,
    YouTubeDownloadError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from AcapellaMakerError."""
        exceptions = [
            AudioLoadError,
            AudioSaveError,
            BPMDetectionError,
            VocalExtractionError,
            SilenceTrimmingError,
            YouTubeDownloadError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, AcapellaMakerError)

    def test_base_exception_inherits_from_exception(self):
        """Test that base exception inherits from built-in Exception."""
        assert issubclass(AcapellaMakerError, Exception)


class TestExceptionMessages:
    """Tests for exception message handling."""

    @pytest.mark.parametrize(
        "exc_class",
        [
            AcapellaMakerError,
            AudioLoadError,
            AudioSaveError,
            BPMDetectionError,
            VocalExtractionError,
            SilenceTrimmingError,
            YouTubeDownloadError,
        ],
    )
    def test_exception_stores_message(self, exc_class):
        """Test that exceptions store their message."""
        message = "Test error message"
        exc = exc_class(message)

        assert str(exc) == message

    @pytest.mark.parametrize(
        "exc_class",
        [
            AcapellaMakerError,
            AudioLoadError,
            AudioSaveError,
            BPMDetectionError,
            VocalExtractionError,
            SilenceTrimmingError,
            YouTubeDownloadError,
        ],
    )
    def test_exception_can_be_raised_and_caught(self, exc_class):
        """Test that exceptions can be raised and caught properly."""
        message = "Test error"

        with pytest.raises(exc_class) as exc_info:
            raise exc_class(message)

        assert str(exc_info.value) == message

    def test_specific_exception_caught_by_base(self):
        """Test that specific exceptions can be caught by base class."""
        with pytest.raises(AcapellaMakerError):
            raise AudioLoadError("File not found")

    def test_exception_chaining(self):
        """Test that exception chaining works properly."""
        original = ValueError("Original error")

        try:
            try:
                raise original
            except ValueError as e:
                raise AudioLoadError("Failed to load") from e
        except AudioLoadError as e:
            assert e.__cause__ is original
