"""Shared test fixtures for Acapella tests."""

import tempfile
from pathlib import Path
from typing import Tuple

import numpy as np
import pytest
import soundfile as sf

# Standard test sample rate
SAMPLE_RATE = 44100


@pytest.fixture
def sample_rate() -> int:
    """Standard test sample rate."""
    return SAMPLE_RATE


@pytest.fixture
def mono_audio() -> np.ndarray:
    """Generate a 1-second mono 440Hz sine wave.

    Returns:
        Mono audio array with shape (samples,).
    """
    duration = 1.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    return (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)


@pytest.fixture
def stereo_audio() -> np.ndarray:
    """Generate a 1-second stereo 440Hz sine wave.

    Returns:
        Stereo audio array with shape (2, samples).
    """
    duration = 1.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    mono = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)
    return np.stack([mono, mono], axis=0)


@pytest.fixture
def silent_audio() -> np.ndarray:
    """Generate 1 second of silence.

    Returns:
        Mono audio array of zeros.
    """
    return np.zeros(SAMPLE_RATE, dtype=np.float32)


@pytest.fixture
def audio_with_leading_silence() -> np.ndarray:
    """Generate audio with 0.5s silence followed by 0.5s of 440Hz tone.

    Returns:
        Mono audio array with leading silence.
    """
    silence = np.zeros(SAMPLE_RATE // 2, dtype=np.float32)
    t = np.linspace(0, 0.5, SAMPLE_RATE // 2, endpoint=False)
    tone = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)
    return np.concatenate([silence, tone])


@pytest.fixture
def stereo_audio_with_leading_silence() -> np.ndarray:
    """Generate stereo audio with 0.5s silence followed by 0.5s of 440Hz tone.

    Returns:
        Stereo audio array with shape (2, samples).
    """
    silence = np.zeros(SAMPLE_RATE // 2, dtype=np.float32)
    t = np.linspace(0, 0.5, SAMPLE_RATE // 2, endpoint=False)
    tone = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)
    mono = np.concatenate([silence, tone])
    return np.stack([mono, mono], axis=0)


@pytest.fixture
def temp_audio_file(mono_audio: np.ndarray, tmp_path: Path) -> Path:
    """Create a temporary WAV file with mono audio.

    Args:
        mono_audio: Mono audio fixture.
        tmp_path: Pytest tmp_path fixture.

    Returns:
        Path to the temporary WAV file.
    """
    file_path = tmp_path / "test_audio.wav"
    sf.write(file_path, mono_audio, SAMPLE_RATE)
    return file_path


@pytest.fixture
def temp_stereo_file(stereo_audio: np.ndarray, tmp_path: Path) -> Path:
    """Create a temporary WAV file with stereo audio.

    Args:
        stereo_audio: Stereo audio fixture.
        tmp_path: Pytest tmp_path fixture.

    Returns:
        Path to the temporary WAV file.
    """
    file_path = tmp_path / "test_stereo.wav"
    # soundfile expects (samples, channels) for stereo
    sf.write(file_path, stereo_audio.T, SAMPLE_RATE)
    return file_path


@pytest.fixture
def mock_demucs(mocker):
    """Mock Demucs model and extract_vocals to avoid loading 300MB model.

    Returns a mock that returns synthetic vocal data.
    """
    # Create mock vocals output (stereo, 1 second)
    mock_vocals = np.zeros((2, SAMPLE_RATE), dtype=np.float32)
    t = np.linspace(0, 1.0, SAMPLE_RATE, endpoint=False)
    mock_vocals[0] = (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)
    mock_vocals[1] = mock_vocals[0]

    mock = mocker.patch("acapella.core.vocal_extractor.extract_vocals")
    mock.return_value = (mock_vocals, SAMPLE_RATE)
    return mock


@pytest.fixture
def mock_extract_vocals(mocker):
    """Mock extract_vocals at the pipeline level."""
    mock_vocals = np.zeros((2, SAMPLE_RATE), dtype=np.float32)
    t = np.linspace(0, 1.0, SAMPLE_RATE, endpoint=False)
    mock_vocals[0] = (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)
    mock_vocals[1] = mock_vocals[0]

    mock = mocker.patch("acapella.core.pipeline.extract_vocals")
    mock.return_value = (mock_vocals, SAMPLE_RATE)
    return mock


@pytest.fixture
def temp_config_dir(tmp_path: Path, monkeypatch):
    """Create a temporary config directory and patch config module to use it.

    Args:
        tmp_path: Pytest tmp_path fixture.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        Path to the temporary config directory.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    monkeypatch.setattr(
        "acapella.config.get_config_dir",
        lambda: config_dir,
    )
    # Reset cached config
    import acapella.config as config_module

    config_module._config = None

    return config_dir


@pytest.fixture
def mock_bpm_detection(mocker):
    """Mock BPM detection to return a fixed value.

    This is useful for tests that don't need real BPM detection,
    since simple test audio (sine waves) may not have detectable rhythm.
    """
    mock = mocker.patch("acapella.core.bpm_detector.detect_bpm")
    mock.return_value = 120.0
    return mock


@pytest.fixture
def mock_pipeline_bpm(mocker):
    """Mock BPM detection at the pipeline level."""
    mock = mocker.patch("acapella.core.pipeline.detect_bpm")
    mock.return_value = 120.0
    return mock
