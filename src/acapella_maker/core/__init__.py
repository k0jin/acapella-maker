"""Core processing modules for Acapella Maker."""

from acapella_maker.core.audio_io import load_audio, save_audio
from acapella_maker.core.bpm_detector import detect_bpm
from acapella_maker.core.pipeline import AcapellaPipeline
from acapella_maker.core.silence_trimmer import trim_silence
from acapella_maker.core.vocal_extractor import extract_vocals
from acapella_maker.core.youtube import download_audio, is_youtube_url

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
