"""Vocal extraction using Demucs."""

import os
import sys
from pathlib import Path
from typing import Tuple, Union

import certifi
import numpy as np
import torch

# Fix SSL certificate issues on macOS (must be set before demucs imports)
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# When running as a bundled app, use bundled model cache
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _bundle_dir = Path(sys._MEIPASS)
    # Models are bundled in hub/checkpoints/, set TORCH_HOME so torch finds them
    if (_bundle_dir / "hub" / "checkpoints").exists():
        os.environ["TORCH_HOME"] = str(_bundle_dir)

from acapella_maker.core.audio_io import DEFAULT_SAMPLE_RATE, load_audio
from acapella_maker.exceptions import VocalExtractionError
from acapella_maker.logging_config import get_logger

logger = get_logger(__name__)


def _prepare_audio(
    audio_or_path: Union[np.ndarray, str, Path],
    sample_rate: int,
    model_samplerate: int,
) -> Tuple[np.ndarray, int]:
    """Prepare audio for Demucs model.

    Args:
        audio_or_path: Audio data or path to audio file.
        sample_rate: Sample rate of input audio data.
        model_samplerate: Required sample rate for the model.

    Returns:
        Tuple of (prepared stereo audio, sample rate).
    """
    import librosa

    # Load audio if path provided
    if isinstance(audio_or_path, (str, Path)):
        input_path = Path(audio_or_path)
        audio, sample_rate = load_audio(input_path, sr=model_samplerate, mono=False)
    else:
        audio = audio_or_path
        # Resample if needed
        if sample_rate != model_samplerate:
            if audio.ndim == 1:
                audio = librosa.resample(
                    audio, orig_sr=sample_rate, target_sr=model_samplerate
                )
            else:
                audio = np.array(
                    [
                        librosa.resample(
                            ch, orig_sr=sample_rate, target_sr=model_samplerate
                        )
                        for ch in audio
                    ]
                )
            sample_rate = model_samplerate

    # Ensure stereo format (channels, samples)
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=0)
    elif audio.shape[0] > 2:
        # (samples, channels) -> (channels, samples)
        audio = audio.T

    return audio, sample_rate


def _run_demucs_model(
    audio: np.ndarray,
    model: torch.nn.Module,
    device: torch.device,
) -> np.ndarray:
    """Run Demucs model to extract vocals.

    Args:
        audio: Stereo audio array with shape (channels, samples).
        model: Loaded Demucs model.
        device: Torch device to run on.

    Returns:
        Extracted vocals array with shape (channels, samples).
    """
    from demucs.apply import apply_model

    # Convert to torch tensor: (batch, channels, samples)
    audio_tensor = torch.from_numpy(audio).float().unsqueeze(0).to(device)

    # Apply model
    with torch.no_grad():
        sources = apply_model(model, audio_tensor, device=device)

    # sources shape: (batch, sources, channels, samples)
    # Source order for htdemucs: drums, bass, other, vocals
    source_names = model.sources
    vocals_idx = source_names.index("vocals")

    return sources[0, vocals_idx].cpu().numpy()


def _resample_output(
    vocals: np.ndarray,
    current_rate: int,
    target_rate: int,
) -> Tuple[np.ndarray, int]:
    """Resample vocals to target sample rate if needed.

    Args:
        vocals: Vocals audio array.
        current_rate: Current sample rate.
        target_rate: Target sample rate.

    Returns:
        Tuple of (resampled vocals, sample rate).
    """
    if current_rate == target_rate:
        return vocals, current_rate

    import librosa

    vocals = np.array(
        [
            librosa.resample(ch, orig_sr=current_rate, target_sr=target_rate)
            for ch in vocals
        ]
    )
    return vocals, target_rate


def extract_vocals(
    audio_or_path: Union[np.ndarray, str, Path],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> Tuple[np.ndarray, int]:
    """Extract vocals from audio using Demucs.

    Args:
        audio_or_path: Audio data or path to audio file.
        sample_rate: Sample rate (only used if audio data provided).

    Returns:
        Tuple of (vocals audio data, sample rate).

    Raises:
        VocalExtractionError: If extraction fails.
    """
    try:
        from demucs.pretrained import get_model

        # Load the htdemucs model (best quality)
        logger.info("Loading Demucs htdemucs model")
        model = get_model("htdemucs")
        model.eval()

        # Use GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Using device: %s", device)
        model.to(device)

        # Prepare audio
        logger.debug(
            "Preparing audio for model (target sample rate: %d)", model.samplerate
        )
        audio, sample_rate = _prepare_audio(
            audio_or_path, sample_rate, model.samplerate
        )

        # Extract vocals
        logger.debug("Running Demucs model")
        vocals = _run_demucs_model(audio, model, device)

        # Resample to default output rate
        logger.debug("Resampling output to %d Hz", DEFAULT_SAMPLE_RATE)
        vocals, sample_rate = _resample_output(vocals, sample_rate, DEFAULT_SAMPLE_RATE)

        logger.info("Vocal extraction successful")
        return vocals, sample_rate

    except VocalExtractionError:
        raise
    except Exception as e:
        raise VocalExtractionError(f"Vocal extraction failed: {e}") from e
