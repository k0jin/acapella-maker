"""Worker thread for acapella extraction."""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from acapella_maker.core.pipeline import AcapellaPipeline
from acapella_maker.core.youtube import download_audio, is_youtube_url
from acapella_maker.models.result import ProcessingOptions, ProcessingResult


class ExtractionWorker(QThread):
    """Worker thread for running acapella extraction."""

    stage_changed = Signal(str)
    progress = Signal(str, float)
    finished_ok = Signal(ProcessingResult)
    error = Signal(str)

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
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the worker."""
        self._cancelled = True

    def _on_progress(self, stage: str, percent: float) -> None:
        """Progress callback for the pipeline.

        Args:
            stage: Current processing stage name.
            percent: Progress percentage (0-100).

        Raises:
            InterruptedError: If the operation was cancelled.
        """
        if self._cancelled:
            raise InterruptedError("Operation cancelled by user")
        self.stage_changed.emit(stage)
        self.progress.emit(stage, percent)

    def run(self) -> None:
        """Run the extraction process."""
        temp_dir: Optional[str] = None
        try:
            audio_path = self.input_path

            # Handle YouTube URL
            if is_youtube_url(self.input_path):
                self.stage_changed.emit("Downloading from YouTube...")
                self.progress.emit("Downloading from YouTube...", 0)

                temp_dir = tempfile.mkdtemp(prefix="acapella_")
                audio_path = str(
                    download_audio(self.input_path, Path(temp_dir))
                )

                if self._cancelled:
                    return

                self.progress.emit("Downloading from YouTube...", 100)

            # Create processing options
            options = ProcessingOptions(
                silence_threshold_db=self.silence_threshold,
                trim_silence=self.trim_silence,
                progress_callback=self._on_progress,
            )

            # Run pipeline
            pipeline = AcapellaPipeline(options)
            result = pipeline.process(audio_path, self.output_path)

            if not self._cancelled:
                self.finished_ok.emit(result)

        except InterruptedError:
            pass  # Cancelled, no error signal
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))
        finally:
            # Clean up temp directory
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)
