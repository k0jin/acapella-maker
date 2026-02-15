"""Audio I/O operations using librosa and soundfile."""

from pathlib import Path
from typing import Tuple, Union

import librosa
import numpy as np
import soundfile as sf

from acapella.exceptions import AudioLoadError, AudioSaveError

DEFAULT_SAMPLE_RATE = 44100


def load_audio(
    path: Union[str, Path],
    sr: int = DEFAULT_SAMPLE_RATE,
    mono: bool = False,
) -> Tuple[np.ndarray, int]:
    """Load audio file.

    Args:
        path: Path to audio file.
        sr: Target sample rate. Use None to preserve original.
        mono: If True, convert to mono.

    Returns:
        Tuple of (audio data, sample rate).
        Audio shape is (samples,) for mono or (channels, samples) for stereo.

    Raises:
        AudioLoadError: If file cannot be loaded.
    """
    path = Path(path)

    if not path.exists():
        raise AudioLoadError(f"File not found: {path}")

    try:
        audio, sample_rate = librosa.load(path, sr=sr, mono=mono)
        return audio, sample_rate
    except Exception as e:
        raise AudioLoadError(f"Failed to load {path}: {e}") from e


def save_audio(
    audio: np.ndarray,
    path: Union[str, Path],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> Path:
    """Save audio to WAV file.

    Args:
        audio: Audio data. Shape (samples,) for mono or (channels, samples) for stereo.
        path: Output path.
        sample_rate: Sample rate.

    Returns:
        Path to saved file.

    Raises:
        AudioSaveError: If file cannot be saved.
    """
    path = Path(path)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        # soundfile expects (samples, channels) for stereo
        if audio.ndim == 2 and audio.shape[0] <= 2:
            audio = audio.T

        sf.write(path, audio, sample_rate)
        return path
    except Exception as e:
        raise AudioSaveError(f"Failed to save {path}: {e}") from e


def get_duration(audio: np.ndarray, sample_rate: int) -> float:
    """Get audio duration in seconds."""
    if audio.ndim == 2:
        samples = audio.shape[1]
    else:
        samples = audio.shape[0]
    return samples / sample_rate
