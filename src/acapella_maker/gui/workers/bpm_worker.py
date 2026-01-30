"""Worker thread for BPM detection only."""

from typing import Optional

from PySide6.QtCore import QThread, Signal

from acapella_maker.core.pipeline import AcapellaPipeline
from acapella_maker.core.youtube import is_youtube_url, youtube_audio
from acapella_maker.gui.workers.base_worker import BaseWorker


class BPMWorker(BaseWorker):
    """Worker thread for BPM-only detection."""

    finished_ok = Signal(float)

    def __init__(self, input_path: str, parent: Optional[QThread] = None) -> None:
        super().__init__(parent)
        self.input_path = input_path

    def _detect_bpm(self, audio_path: str) -> None:
        """Detect BPM from audio file."""
        self.stage_changed.emit("Detecting BPM...")
        self.progress.emit("Detecting BPM...", 0)

        if self._cancelled:
            return

        pipeline = AcapellaPipeline()
        bpm = pipeline.detect_bpm_only(audio_path)

        self.progress.emit("Detecting BPM...", 100)

        if not self._cancelled:
            self.finished_ok.emit(bpm)

    def run(self) -> None:
        """Run BPM detection."""
        try:
            if is_youtube_url(self.input_path):
                self.stage_changed.emit("Downloading from YouTube...")
                self.progress.emit("Downloading from YouTube...", 0)

                with youtube_audio(self.input_path) as audio_path:
                    if self._cancelled:
                        return
                    self.progress.emit("Downloading from YouTube...", 100)
                    self._detect_bpm(str(audio_path))
            else:
                self._detect_bpm(self.input_path)

        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))
