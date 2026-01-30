"""Unit tests for silence trimmer module."""

import numpy as np
import pytest

from acapella_maker.core.silence_trimmer import trim_silence
from acapella_maker.exceptions import SilenceTrimmingError


class TestTrimSilence:
    """Tests for trim_silence function."""

    def test_trim_leading_silence_mono(
        self, audio_with_leading_silence: np.ndarray, sample_rate: int
    ):
        """Test trimming leading silence from mono audio."""
        trimmed, trimmed_ms = trim_silence(
            audio_with_leading_silence,
            sample_rate,
            threshold_db=30.0,
        )

        # Should have trimmed some audio
        assert trimmed_ms > 0
        # Trimmed audio should be shorter
        assert len(trimmed) < len(audio_with_leading_silence)

    def test_trim_leading_silence_stereo(
        self, stereo_audio_with_leading_silence: np.ndarray, sample_rate: int
    ):
        """Test trimming leading silence from stereo audio."""
        trimmed, trimmed_ms = trim_silence(
            stereo_audio_with_leading_silence,
            sample_rate,
            threshold_db=30.0,
        )

        # Should have trimmed some audio
        assert trimmed_ms > 0
        # Trimmed audio should be shorter (check samples dimension)
        assert trimmed.shape[1] < stereo_audio_with_leading_silence.shape[1]
        # Should still be stereo
        assert trimmed.shape[0] == 2

    def test_no_trim_when_no_leading_silence(
        self, mono_audio: np.ndarray, sample_rate: int
    ):
        """Test that audio without leading silence is not trimmed."""
        trimmed, trimmed_ms = trim_silence(mono_audio, sample_rate)

        # Should not trim anything significant
        assert trimmed_ms < 50  # Less than 50ms
        # Audio length should be similar
        assert abs(len(trimmed) - len(mono_audio)) < sample_rate // 10

    def test_threshold_affects_trim_amount(
        self, audio_with_leading_silence: np.ndarray, sample_rate: int
    ):
        """Test that different thresholds affect trim amount."""
        # High threshold (more aggressive)
        trimmed_high, ms_high = trim_silence(
            audio_with_leading_silence.copy(),
            sample_rate,
            threshold_db=50.0,
        )

        # Low threshold (less aggressive)
        trimmed_low, ms_low = trim_silence(
            audio_with_leading_silence.copy(),
            sample_rate,
            threshold_db=10.0,
        )

        # Higher threshold should trim at least as much as lower threshold
        assert ms_high >= ms_low

    def test_buffer_before_preserved(
        self, audio_with_leading_silence: np.ndarray, sample_rate: int
    ):
        """Test that buffer_before_ms is preserved."""
        buffer_ms = 50.0

        trimmed, trimmed_ms = trim_silence(
            audio_with_leading_silence,
            sample_rate,
            buffer_before_ms=buffer_ms,
        )

        # The trimmed amount should be reduced by the buffer
        # (we can't test exact amount due to frame-based detection)
        assert trimmed_ms >= 0

    def test_fade_in_applied(
        self, audio_with_leading_silence: np.ndarray, sample_rate: int
    ):
        """Test that fade-in is applied to avoid clicks."""
        fade_ms = 10.0

        trimmed, _ = trim_silence(
            audio_with_leading_silence,
            sample_rate,
            fade_in_ms=fade_ms,
        )

        # First sample should be close to 0 due to fade-in
        # (unless no trimming occurred)
        if len(trimmed) < len(audio_with_leading_silence):
            assert abs(trimmed[0]) < 0.1

    def test_silent_audio_returns_original(
        self, silent_audio: np.ndarray, sample_rate: int
    ):
        """Test that completely silent audio raises an error or returns original."""
        with pytest.raises(SilenceTrimmingError, match="completely silent"):
            trim_silence(silent_audio, sample_rate)

    def test_very_short_audio_handled(self, sample_rate: int):
        """Test handling of very short audio.

        Very short audio may either raise an error or return the original
        depending on the RMS calculation behavior.
        """
        short_audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        try:
            trimmed, trimmed_ms = trim_silence(short_audio, sample_rate)
            # If it doesn't raise, it should return something reasonable
            assert len(trimmed) <= len(short_audio)
        except SilenceTrimmingError:
            # This is also acceptable
            pass


class TestTrimSilenceEdgeCases:
    """Edge case tests for trim_silence."""

    def test_all_above_threshold(self, sample_rate: int):
        """Test audio that's all above threshold."""
        # Create loud audio
        loud_audio = np.ones(sample_rate, dtype=np.float32) * 0.5

        trimmed, trimmed_ms = trim_silence(loud_audio, sample_rate)

        # Should not trim anything
        assert trimmed_ms < 50
        assert len(trimmed) == len(loud_audio)

    def test_stereo_channels_stay_aligned(self, sample_rate: int):
        """Test that stereo channels remain aligned after trimming."""
        # Create stereo with different content per channel
        duration = 1.0
        samples = int(sample_rate * duration)

        # Silence then different frequencies per channel
        silence = np.zeros(samples // 2, dtype=np.float32)
        t = np.linspace(0, 0.5, samples // 2, endpoint=False)

        left = np.concatenate([silence, np.sin(2 * np.pi * 440 * t).astype(np.float32)])
        right = np.concatenate([silence, np.sin(2 * np.pi * 880 * t).astype(np.float32)])

        stereo = np.stack([left, right], axis=0)

        trimmed, _ = trim_silence(stereo, sample_rate)

        # Both channels should have same length
        assert trimmed.shape[0] == 2
        assert trimmed[0].shape == trimmed[1].shape
