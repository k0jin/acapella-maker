"""Worker thread for acapella extraction."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from acapella.core.pipeline import AcapellaPipeline
from acapella.core.youtube import is_youtube_url, youtube_audio
from acapella.gui.workers.base_worker import BaseWorker
from acapella.models.result import ProcessingOptions, ProcessingResult


class ExtractionWorker(BaseWorker):
    """Worker thread for running acapella extraction."""

    bpm_detected = Signal(int)
    finished_ok = Signal(ProcessingResult)

    # Progress phase ranges for YouTube flow
    PHASE_DOWNLOAD = (0, 20)
    PHASE_BPM = (20, 30)
    PHASE_EXTRACT = (30, 90)
    PHASE_SAVE = (90, 100)

    # Progress phase ranges for local file flow
    PHASE_BPM_LOCAL = (0, 15)
    PHASE_EXTRACT_LOCAL = (15, 85)
    PHASE_SAVE_LOCAL = (85, 100)

    def __init__(
        self,
        input_path: str,
        output_path: str,
        silence_threshold: float = 30.0,
        trim_silence: bool = True,
        parent: Optional[QThread] = None,
    ) -> None:
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.silence_threshold = silence_threshold
        self.trim_silence = trim_silence
        self._is_youtube = is_youtube_url(input_path)

    def _map_progress(
        self, phase_range: tuple[int, int], local_percent: float
    ) -> float:
        """Map local progress (0-100) to overall progress within a phase range."""
        start, end = phase_range
        return start + (local_percent / 100) * (end - start)

    def _on_download_progress(self, percent: float) -> None:
        """Progress callback for YouTube download phase."""
        if self._cancelled:
            raise InterruptedError("Operation cancelled by user")
        overall = self._map_progress(self.PHASE_DOWNLOAD, percent)
        self.progress.emit("Downloading from YouTube...", overall)

    def _on_progress(self, stage: str, percent: float) -> None:
        """Progress callback for the pipeline (extraction phase)."""
        if self._cancelled:
            raise InterruptedError("Operation cancelled by user")
        self.stage_changed.emit(stage)
        # Map pipeline progress to extraction phase range
        phase = self.PHASE_EXTRACT if self._is_youtube else self.PHASE_EXTRACT_LOCAL
        overall = self._map_progress(phase, percent)
        self.progress.emit(stage, overall)

    def _process_audio(self, audio_path: str) -> None:
        """Process audio file (extraction logic)."""
        # Detect BPM first (before full pipeline)
        bpm_phase = self.PHASE_BPM if self._is_youtube else self.PHASE_BPM_LOCAL
        self.stage_changed.emit("Detecting BPM")
        self.progress.emit("Detecting BPM", bpm_phase[0])
        pipeline = AcapellaPipeline()
        bpm = pipeline.detect_bpm_only(audio_path)
        bpm_int = round(bpm)
        self.bpm_detected.emit(bpm_int)
        self.progress.emit("Detecting BPM", bpm_phase[1])

        if self._cancelled:
            return

        # Modify output path to include BPM suffix (before extension)
        output_path = Path(self.output_path)
        new_filename = f"{output_path.stem}_{bpm_int}bpm{output_path.suffix}"
        final_output_path = str(output_path.parent / new_filename)

        # Create processing options with pre-detected BPM to skip redundant detection
        options = ProcessingOptions(
            silence_threshold_db=self.silence_threshold,
            trim_silence=self.trim_silence,
            pre_detected_bpm=bpm,
            progress_callback=self._on_progress,
        )

        # Run pipeline
        pipeline = AcapellaPipeline(options)
        result = pipeline.process(audio_path, final_output_path)

        if not self._cancelled:
            self.finished_ok.emit(result)

    def run(self) -> None:
        """Run the extraction process."""
        try:
            if self._is_youtube:
                self.stage_changed.emit("Downloading from YouTube...")
                self.progress.emit("Downloading from YouTube...", 0)

                with youtube_audio(
                    self.input_path, self._on_download_progress
                ) as audio_path:
                    if self._cancelled:
                        return
                    self.progress.emit(
                        "Downloading from YouTube...", self.PHASE_DOWNLOAD[1]
                    )
                    self._process_audio(str(audio_path))
            else:
                self._process_audio(self.input_path)

        except InterruptedError:
            pass  # Cancelled, no error signal
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))
