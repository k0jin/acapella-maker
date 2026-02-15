"""Acapella - Extract vocals from audio files."""

__version__ = "0.1.0"

from acapella.core.pipeline import AcapellaPipeline
from acapella.models.result import ProcessingOptions, ProcessingResult

__all__ = ["AcapellaPipeline", "ProcessingOptions", "ProcessingResult", "__version__"]
