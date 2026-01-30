"""Unit tests for audio I/O module."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from acapella_maker.core.audio_io import (
    DEFAULT_SAMPLE_RATE,
    get_duration,
    load_audio,
    save_audio,
)
from acapella_maker.exceptions import AudioLoadError, AudioSaveError


class TestLoadAudio:
    """Tests for load_audio function."""

    def test_load_mono_file(self, temp_audio_file: Path, sample_rate: int):
        """Test loading a mono WAV file."""
        audio, sr = load_audio(temp_audio_file, mono=True)

        assert sr == sample_rate
        assert audio.ndim == 1
        assert len(audio) > 0

    def test_load_stereo_file(self, temp_stereo_file: Path, sample_rate: int):
        """Test loading a stereo WAV file."""
        audio, sr = load_audio(temp_stereo_file, mono=False)

        assert sr == sample_rate
        assert audio.ndim == 2
        assert audio.shape[0] == 2  # 2 channels

    def test_load_file_not_found(self, tmp_path: Path):
        """Test loading a non-existent file raises AudioLoadError."""
        fake_path = tmp_path / "nonexistent.wav"

        with pytest.raises(AudioLoadError, match="File not found"):
            load_audio(fake_path)

    def test_load_invalid_file(self, tmp_path: Path):
        """Test loading an invalid audio file raises AudioLoadError."""
        invalid_file = tmp_path / "invalid.wav"
        invalid_file.write_text("not audio data")

        with pytest.raises(AudioLoadError):
            load_audio(invalid_file)

    def test_load_with_resample(self, temp_audio_file: Path):
        """Test loading with a different sample rate."""
        target_sr = 22050
        audio, sr = load_audio(temp_audio_file, sr=target_sr)

        assert sr == target_sr


class TestSaveAudio:
    """Tests for save_audio function."""

    def test_save_mono_audio(self, mono_audio: np.ndarray, tmp_path: Path, sample_rate: int):
        """Test saving mono audio to file."""
        output_path = tmp_path / "output.wav"
        result = save_audio(mono_audio, output_path, sample_rate)

        assert result == output_path
        assert output_path.exists()

        # Verify content
        loaded, sr = sf.read(output_path)
        assert sr == sample_rate
        assert loaded.shape[0] == len(mono_audio)

    def test_save_stereo_audio(self, stereo_audio: np.ndarray, tmp_path: Path, sample_rate: int):
        """Test saving stereo audio to file."""
        output_path = tmp_path / "stereo_output.wav"
        result = save_audio(stereo_audio, output_path, sample_rate)

        assert result == output_path
        assert output_path.exists()

        # Verify content
        loaded, sr = sf.read(output_path)
        assert sr == sample_rate
        assert loaded.ndim == 2
        assert loaded.shape[1] == 2  # 2 channels

    def test_save_creates_parent_dirs(self, mono_audio: np.ndarray, tmp_path: Path, sample_rate: int):
        """Test that save_audio creates parent directories."""
        output_path = tmp_path / "nested" / "dirs" / "output.wav"
        result = save_audio(mono_audio, output_path, sample_rate)

        assert result == output_path
        assert output_path.exists()


class TestGetDuration:
    """Tests for get_duration function."""

    def test_mono_duration(self, mono_audio: np.ndarray, sample_rate: int):
        """Test duration calculation for mono audio."""
        duration = get_duration(mono_audio, sample_rate)
        assert abs(duration - 1.0) < 0.01  # 1 second

    def test_stereo_duration(self, stereo_audio: np.ndarray, sample_rate: int):
        """Test duration calculation for stereo audio."""
        duration = get_duration(stereo_audio, sample_rate)
        assert abs(duration - 1.0) < 0.01  # 1 second


class TestDefaultSampleRate:
    """Tests for default sample rate constant."""

    def test_default_sample_rate_is_44100(self):
        """Test that default sample rate is 44100 Hz."""
        assert DEFAULT_SAMPLE_RATE == 44100
