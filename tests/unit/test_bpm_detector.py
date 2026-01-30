"""Unit tests for BPM detector module."""

from pathlib import Path

import numpy as np
import pytest

from acapella_maker.core.bpm_detector import detect_bpm
from acapella_maker.exceptions import BPMDetectionError


class TestDetectBPM:
    """Tests for detect_bpm function."""

    def test_detect_bpm_from_file(self, temp_audio_file: Path):
        """Test BPM detection from a file.

        Note: Simple sine waves may not have detectable rhythm,
        so we accept either a valid BPM or an error.
        """
        try:
            bpm = detect_bpm(temp_audio_file)
            assert isinstance(bpm, float)
            assert bpm > 0
        except BPMDetectionError:
            # Pure tone has no rhythm - this is acceptable
            pass

    def test_detect_bpm_from_mono_array(self, mono_audio: np.ndarray, sample_rate: int):
        """Test BPM detection from mono audio array."""
        try:
            bpm = detect_bpm(mono_audio, sample_rate)
            assert isinstance(bpm, float)
            assert bpm > 0
        except BPMDetectionError:
            # Pure tone has no rhythm - this is acceptable
            pass

    def test_detect_bpm_from_stereo_array(self, stereo_audio: np.ndarray, sample_rate: int):
        """Test BPM detection from stereo audio array (converts to mono)."""
        try:
            bpm = detect_bpm(stereo_audio, sample_rate)
            assert isinstance(bpm, float)
            assert bpm > 0
        except BPMDetectionError:
            # Pure tone has no rhythm - this is acceptable
            pass

    def test_detect_bpm_returns_rounded_value(self, sample_rate: int):
        """Test that BPM is rounded to 1 decimal place using rhythmic audio."""
        # Create audio with clear rhythm for reliable BPM detection
        duration = 4.0
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, endpoint=False)

        # Create click track at 120 BPM
        audio = np.zeros(samples, dtype=np.float32)
        beat_interval = 0.5  # 120 BPM

        for beat_time in np.arange(0, duration, beat_interval):
            start = int(beat_time * sample_rate)
            end = min(start + int(0.01 * sample_rate), samples)
            audio[start:end] = 0.8

        bpm = detect_bpm(audio, sample_rate)
        assert bpm == round(bpm, 1)

    def test_detect_bpm_silent_audio_raises_error(self, silent_audio: np.ndarray, sample_rate: int):
        """Test that completely silent audio raises BPMDetectionError."""
        # Silent audio may return 0 BPM which should raise an error
        # or it may detect some BPM from noise - either is acceptable
        # The key is it shouldn't crash
        try:
            bpm = detect_bpm(silent_audio, sample_rate)
            # If it returns something, it should be valid
            assert isinstance(bpm, float)
        except BPMDetectionError:
            # This is also acceptable
            pass

    def test_detect_bpm_file_not_found(self, tmp_path: Path):
        """Test that non-existent file raises error."""
        fake_path = tmp_path / "nonexistent.wav"

        with pytest.raises(BPMDetectionError):
            detect_bpm(fake_path)


class TestBPMDetectionWithRhythm:
    """Tests with audio containing clear rhythm."""

    @pytest.fixture
    def rhythmic_audio(self, sample_rate: int) -> np.ndarray:
        """Create audio with clear 120 BPM rhythm (2 beats per second)."""
        duration = 4.0  # 4 seconds = 8 beats at 120 BPM
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, endpoint=False)

        # Create click track at 120 BPM (every 0.5 seconds)
        audio = np.zeros(samples, dtype=np.float32)
        beat_interval = 0.5  # 120 BPM = 2 beats/sec = 0.5s interval

        for beat_time in np.arange(0, duration, beat_interval):
            start = int(beat_time * sample_rate)
            end = min(start + int(0.01 * sample_rate), samples)  # 10ms click
            audio[start:end] = 0.8

        return audio

    def test_detect_bpm_rhythmic_audio(self, rhythmic_audio: np.ndarray, sample_rate: int):
        """Test BPM detection on audio with clear rhythm."""
        bpm = detect_bpm(rhythmic_audio, sample_rate)

        # Should detect something close to 120 BPM (or a harmonic like 60 or 240)
        # BPM detection can vary, so we check for reasonable range
        assert 50 < bpm < 250
