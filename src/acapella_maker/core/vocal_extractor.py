"""Vocal extraction using Demucs."""

import os
import ssl
import tempfile
from pathlib import Path
from typing import Tuple, Union

import certifi
import numpy as np
import torch

# Fix SSL certificate issues on macOS
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from acapella_maker.core.audio_io import DEFAULT_SAMPLE_RATE, load_audio, save_audio
from acapella_maker.exceptions import VocalExtractionError


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
        # Import demucs here to defer loading
        from demucs.apply import apply_model
        from demucs.pretrained import get_model

        # Load the htdemucs model (best quality)
        model = get_model("htdemucs")
        model.eval()

        # Use GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)

        # Handle input
        if isinstance(audio_or_path, (str, Path)):
            input_path = Path(audio_or_path)
            audio, sample_rate = load_audio(input_path, sr=model.samplerate, mono=False)
        else:
            audio = audio_or_path
            # Resample if needed
            if sample_rate != model.samplerate:
                import librosa
                if audio.ndim == 1:
                    audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=model.samplerate)
                else:
                    audio = np.array([
                        librosa.resample(ch, orig_sr=sample_rate, target_sr=model.samplerate)
                        for ch in audio
                    ])
                sample_rate = model.samplerate

        # Ensure stereo
        if audio.ndim == 1:
            audio = np.stack([audio, audio], axis=0)
        elif audio.shape[0] > 2:
            # (samples, channels) -> (channels, samples)
            audio = audio.T

        # Convert to torch tensor: (batch, channels, samples)
        audio_tensor = torch.from_numpy(audio).float().unsqueeze(0).to(device)

        # Apply model
        with torch.no_grad():
            sources = apply_model(model, audio_tensor, device=device)

        # sources shape: (batch, sources, channels, samples)
        # Source order for htdemucs: drums, bass, other, vocals
        source_names = model.sources
        vocals_idx = source_names.index("vocals")

        vocals = sources[0, vocals_idx].cpu().numpy()

        # Resample back to original sample rate if needed
        if sample_rate != DEFAULT_SAMPLE_RATE:
            import librosa
            vocals = np.array([
                librosa.resample(ch, orig_sr=sample_rate, target_sr=DEFAULT_SAMPLE_RATE)
                for ch in vocals
            ])
            sample_rate = DEFAULT_SAMPLE_RATE

        return vocals, sample_rate

    except VocalExtractionError:
        raise
    except Exception as e:
        raise VocalExtractionError(f"Vocal extraction failed: {e}") from e
