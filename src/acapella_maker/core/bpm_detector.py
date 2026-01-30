"""BPM detection using librosa."""

from pathlib import Path
from typing import Union

import librosa
import numpy as np

from acapella_maker.core.audio_io import DEFAULT_SAMPLE_RATE, load_audio
from acapella_maker.exceptions import BPMDetectionError


def detect_bpm(
    audio_or_path: Union[np.ndarray, str, Path],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> float:
    """Detect BPM from audio.

    Args:
        audio_or_path: Audio data (mono) or path to audio file.
        sample_rate: Sample rate (only used if audio data provided).

    Returns:
        Detected BPM as float.

    Raises:
        BPMDetectionError: If BPM cannot be detected.
    """
    try:
        # Load audio if path provided
        if isinstance(audio_or_path, (str, Path)):
            audio, sample_rate = load_audio(audio_or_path, mono=True)
        else:
            audio = audio_or_path
            # Convert to mono if stereo
            if audio.ndim == 2:
                audio = librosa.to_mono(audio)

        # Detect tempo using librosa's beat tracker
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sample_rate)

        # Handle both scalar and array returns (librosa version differences)
        if isinstance(tempo, np.ndarray):
            tempo = float(tempo[0]) if len(tempo) > 0 else 0.0
        else:
            tempo = float(tempo)

        if tempo <= 0:
            raise BPMDetectionError("Could not detect valid BPM")

        return round(tempo, 1)

    except BPMDetectionError:
        raise
    except Exception as e:
        raise BPMDetectionError(f"BPM detection failed: {e}") from e
