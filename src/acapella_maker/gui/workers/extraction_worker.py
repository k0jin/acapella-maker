"""Worker thread for acapella extraction."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from acapella_maker.core.pipeline import AcapellaPipeline
from acapella_maker.core.youtube import is_youtube_url, youtube_audio
from acapella_maker.gui.workers.base_worker import BaseWorker
from acapella_maker.models.result import ProcessingOptions, ProcessingResult


class ExtractionWorker(BaseWorker):
    """Worker thread for running acapella extraction."""

    bpm_detected = Signal(int)
    finished_ok = Signal(ProcessingResult)

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

    def _on_progress(self, stage: str, percent: float) -> None:
        """Progress callback for the pipeline."""
        if self._cancelled:
            raise InterruptedError("Operation cancelled by user")
        self.stage_changed.emit(stage)
        self.progress.emit(stage, percent)

    def _process_audio(self, audio_path: str) -> None:
        """Process audio file (extraction logic)."""
        # Detect BPM first (before full pipeline)
        self.stage_changed.emit("Detecting BPM")
        self.progress.emit("Detecting BPM", 0)
        pipeline = AcapellaPipeline()
        bpm = pipeline.detect_bpm_only(audio_path)
        bpm_int = round(bpm)
        self.bpm_detected.emit(bpm_int)
        self.progress.emit("Detecting BPM", 100)

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
            if is_youtube_url(self.input_path):
                self.stage_changed.emit("Downloading from YouTube...")
                self.progress.emit("Downloading from YouTube...", 0)

                with youtube_audio(self.input_path) as audio_path:
                    if self._cancelled:
                        return
                    self.progress.emit("Downloading from YouTube...", 100)
                    self._process_audio(str(audio_path))
            else:
                self._process_audio(self.input_path)

        except InterruptedError:
            pass  # Cancelled, no error signal
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))
