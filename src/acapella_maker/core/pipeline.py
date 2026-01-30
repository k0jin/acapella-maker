"""Main processing pipeline for acapella extraction."""

from pathlib import Path
from typing import Callable, Optional, Union

from acapella_maker.core.audio_io import get_duration, load_audio, save_audio
from acapella_maker.core.bpm_detector import detect_bpm
from acapella_maker.core.silence_trimmer import trim_silence
from acapella_maker.core.vocal_extractor import extract_vocals
from acapella_maker.models.result import ProcessingOptions, ProcessingResult


class AcapellaPipeline:
    """Pipeline for extracting acapella vocals from audio files."""

    def __init__(self, options: Optional[ProcessingOptions] = None):
        """Initialize pipeline.

        Args:
            options: Processing options. Uses defaults if not provided.
        """
        self.options = options or ProcessingOptions()

    def _report_progress(self, stage: str, percent: float) -> None:
        """Report progress if callback is set."""
        if self.options.progress_callback:
            self.options.progress_callback(stage, percent)

    def process(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
    ) -> ProcessingResult:
        """Process audio file to extract acapella.

        Args:
            input_path: Path to input audio file.
            output_path: Path for output WAV file.
                        Defaults to <input>_acapella.wav

        Returns:
            ProcessingResult with details of the operation.
        """
        input_path = Path(input_path)

        # Generate default output path if not provided
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_acapella.wav"
        else:
            output_path = Path(output_path)

        # Step 1: Detect BPM from original track
        self._report_progress("Detecting BPM", 0)
        bpm = detect_bpm(input_path)
        self._report_progress("Detecting BPM", 100)

        # Step 2: Extract vocals
        self._report_progress("Extracting vocals", 0)
        vocals, sample_rate = extract_vocals(input_path)
        self._report_progress("Extracting vocals", 100)

        original_duration = get_duration(vocals, sample_rate)
        trimmed_ms = 0.0

        # Step 3: Trim leading silence (if enabled)
        if self.options.trim_silence:
            self._report_progress("Trimming silence", 0)
            vocals, trimmed_ms = trim_silence(
                vocals,
                sample_rate,
                threshold_db=self.options.silence_threshold_db,
                buffer_before_ms=self.options.buffer_before_ms,
                fade_in_ms=self.options.fade_in_ms,
            )
            self._report_progress("Trimming silence", 100)

        trimmed_duration = get_duration(vocals, sample_rate)

        # Step 4: Save output
        self._report_progress("Saving", 0)
        save_audio(vocals, output_path, sample_rate)
        self._report_progress("Saving", 100)

        return ProcessingResult(
            input_path=input_path,
            output_path=output_path,
            bpm=bpm,
            original_duration=original_duration,
            trimmed_duration=trimmed_duration,
            silence_trimmed_ms=trimmed_ms,
            sample_rate=sample_rate,
        )

    def detect_bpm_only(self, input_path: Union[str, Path]) -> float:
        """Detect BPM without extracting vocals.

        Args:
            input_path: Path to audio file.

        Returns:
            Detected BPM.
        """
        return detect_bpm(input_path)
