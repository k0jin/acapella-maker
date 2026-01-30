"""Worker thread for BPM detection only."""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from acapella_maker.core.pipeline import AcapellaPipeline
from acapella_maker.core.youtube import download_audio, is_youtube_url


class BPMWorker(QThread):
    """Worker thread for BPM-only detection."""

    stage_changed = Signal(str)
    progress = Signal(str, float)
    finished_ok = Signal(float)  # BPM value
    error = Signal(str)

    def __init__(self, input_path: str, parent: Optional[QThread] = None) -> None:
        super().__init__(parent)
        self.input_path = input_path
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the worker."""
        self._cancelled = True

    def run(self) -> None:
        """Run BPM detection."""
        temp_dir: Optional[str] = None
        try:
            audio_path = self.input_path

            # Handle YouTube URL
            if is_youtube_url(self.input_path):
                self.stage_changed.emit("Downloading from YouTube...")
                self.progress.emit("Downloading from YouTube...", 0)

                temp_dir = tempfile.mkdtemp(prefix="acapella_bpm_")
                audio_path = str(
                    download_audio(self.input_path, Path(temp_dir))
                )

                if self._cancelled:
                    return

                self.progress.emit("Downloading from YouTube...", 100)

            self.stage_changed.emit("Detecting BPM...")
            self.progress.emit("Detecting BPM...", 0)

            if self._cancelled:
                return

            pipeline = AcapellaPipeline()
            bpm = pipeline.detect_bpm_only(audio_path)

            self.progress.emit("Detecting BPM...", 100)

            if not self._cancelled:
                self.finished_ok.emit(bpm)

        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))
        finally:
            # Clean up temp directory
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)
