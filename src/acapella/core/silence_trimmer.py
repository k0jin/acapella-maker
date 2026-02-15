"""Silence trimming using RMS-based detection."""

from typing import Tuple

import librosa
import numpy as np

from acapella.exceptions import SilenceTrimmingError


def trim_silence(
    audio: np.ndarray,
    sample_rate: int,
    threshold_db: float = 30.0,
    frame_length: int = 2048,
    hop_length: int = 512,
    buffer_before_ms: float = 10.0,
    fade_in_ms: float = 5.0,
) -> Tuple[np.ndarray, float]:
    """Trim leading silence from audio.

    Args:
        audio: Audio data. Shape (samples,) for mono or (channels, samples) for stereo.
        sample_rate: Sample rate.
        threshold_db: Silence threshold in dB below peak RMS.
        frame_length: RMS frame length in samples.
        hop_length: RMS hop length in samples.
        buffer_before_ms: Buffer to keep before first sound (ms).
        fade_in_ms: Fade-in duration to avoid clicks (ms).

    Returns:
        Tuple of (trimmed audio, milliseconds trimmed).

    Raises:
        SilenceTrimmingError: If trimming fails.
    """
    try:
        # Convert to mono for analysis
        if audio.ndim == 2:
            mono = librosa.to_mono(audio)
            is_stereo = True
        else:
            mono = audio
            is_stereo = False

        # Calculate RMS envelope
        rms = librosa.feature.rms(
            y=mono,
            frame_length=frame_length,
            hop_length=hop_length,
        )[0]

        if len(rms) == 0:
            raise SilenceTrimmingError("Audio too short for RMS analysis")

        # Find reference RMS (max) and calculate threshold
        ref_rms = np.max(rms)
        if ref_rms == 0:
            raise SilenceTrimmingError("Audio is completely silent")

        threshold = ref_rms * (10 ** (-threshold_db / 20))

        # Find first frame exceeding threshold
        above_threshold = np.where(rms > threshold)[0]
        if len(above_threshold) == 0:
            # No sound above threshold, return original
            return audio, 0.0

        first_frame = above_threshold[0]

        # Convert frame to sample position
        first_sample = first_frame * hop_length

        # Calculate buffer in samples
        buffer_samples = int(buffer_before_ms * sample_rate / 1000)
        trim_start = max(0, first_sample - buffer_samples)

        # Calculate how much was trimmed
        trimmed_ms = (trim_start / sample_rate) * 1000

        if trim_start == 0:
            return audio, 0.0

        # Trim audio
        if is_stereo:
            trimmed = audio[:, trim_start:]
        else:
            trimmed = audio[trim_start:]

        # Apply fade-in to avoid clicks
        fade_samples = int(fade_in_ms * sample_rate / 1000)
        if fade_samples > 0 and fade_samples < trimmed.shape[-1]:
            fade_curve = np.linspace(0, 1, fade_samples)
            if is_stereo:
                trimmed[:, :fade_samples] *= fade_curve
            else:
                trimmed[:fade_samples] *= fade_curve

        return trimmed, trimmed_ms

    except SilenceTrimmingError:
        raise
    except Exception as e:
        raise SilenceTrimmingError(f"Silence trimming failed: {e}") from e
