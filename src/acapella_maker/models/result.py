"""Data classes for processing options and results."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass
class ProcessingOptions:
    """Options for audio processing pipeline."""

    silence_threshold_db: float = 30.0
    trim_silence: bool = True
    fade_in_ms: float = 5.0
    buffer_before_ms: float = 10.0
    progress_callback: Optional[Callable[[str, float], None]] = field(
        default=None, repr=False
    )


@dataclass
class ProcessingResult:
    """Result of audio processing."""

    input_path: Path
    output_path: Path
    bpm: float
    original_duration: float
    trimmed_duration: float
    silence_trimmed_ms: float
    sample_rate: int

    @property
    def duration_change(self) -> float:
        """Duration change in seconds (negative means trimmed)."""
        return self.trimmed_duration - self.original_duration
