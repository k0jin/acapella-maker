"""Worker thread for BPM detection only."""

from typing import Optional

from PySide6.QtCore import QThread, Signal

from acapella.core.pipeline import AcapellaPipeline
from acapella.core.youtube import is_youtube_url, youtube_audio
from acapella.gui.workers.base_worker import BaseWorker


class BPMWorker(BaseWorker):
    """Worker thread for BPM-only detection."""

    bpm_detected = Signal(int)
    finished_ok = Signal(float)

    # Progress phase ranges for YouTube flow
    PHASE_DOWNLOAD = (0, 70)
    PHASE_BPM = (70, 100)

    # Progress phase range for local file flow
    PHASE_BPM_LOCAL = (0, 100)

    def __init__(self, input_path: str, parent: Optional[QThread] = None) -> None:
        super().__init__(parent)
        self.input_path = input_path
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

    def _detect_bpm(self, audio_path: str) -> None:
        """Detect BPM from audio file."""
        bpm_phase = self.PHASE_BPM if self._is_youtube else self.PHASE_BPM_LOCAL
        self.stage_changed.emit("Detecting BPM...")
        self.progress.emit("Detecting BPM...", bpm_phase[0])

        if self._cancelled:
            return

        pipeline = AcapellaPipeline()
        bpm = pipeline.detect_bpm_only(audio_path)

        self.progress.emit("Detecting BPM...", bpm_phase[1])

        if not self._cancelled:
            bpm_int = round(bpm)
            self.bpm_detected.emit(bpm_int)
            self.finished_ok.emit(bpm)

    def run(self) -> None:
        """Run BPM detection."""
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
                    self._detect_bpm(str(audio_path))
            else:
                self._detect_bpm(self.input_path)

        except InterruptedError:
            pass  # Cancelled, no error signal
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))
