"""Acapella Maker - Extract vocals from audio files."""

__version__ = "0.1.0"

from acapella_maker.core.pipeline import AcapellaPipeline
from acapella_maker.models.result import ProcessingOptions, ProcessingResult

__all__ = ["AcapellaPipeline", "ProcessingOptions", "ProcessingResult", "__version__"]
