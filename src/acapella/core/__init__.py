"""Core processing modules for Acapella."""

from acapella.core.audio_io import load_audio, save_audio
from acapella.core.bpm_detector import detect_bpm
from acapella.core.pipeline import AcapellaPipeline
from acapella.core.silence_trimmer import trim_silence
from acapella.core.vocal_extractor import extract_vocals
from acapella.core.youtube import download_audio, is_youtube_url

__all__ = [
    "AcapellaPipeline",
    "load_audio",
    "save_audio",
    "detect_bpm",
    "extract_vocals",
    "trim_silence",
    "download_audio",
    "is_youtube_url",
]
