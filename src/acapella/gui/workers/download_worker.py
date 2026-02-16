"""Worker thread for downloading YouTube audio to disk."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from acapella.core.youtube import download_audio
from acapella.gui.workers.base_worker import BaseWorker


class DownloadWorker(BaseWorker):
    """Worker thread for downloading YouTube audio without extraction."""

    finished_ok = Signal(str)

    def __init__(
        self, url: str, output_dir: Path, parent: Optional[QThread] = None
    ) -> None:
        super().__init__(parent)
        self.url = url
        self.output_dir = output_dir

    def _on_download_progress(self, percent: float) -> None:
        """Progress callback for YouTube download."""
        if self._cancelled:
            raise InterruptedError("Operation cancelled by user")
        self.progress.emit("Downloading from YouTube...", percent)

    def run(self) -> None:
        """Run the download."""
        try:
            self.stage_changed.emit("Downloading from YouTube...")
            self.progress.emit("Downloading from YouTube...", 0)

            downloaded_path = download_audio(
                self.url, self.output_dir, self._on_download_progress
            )

            if not self._cancelled:
                self.finished_ok.emit(str(downloaded_path))

        except InterruptedError:
            pass
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))
