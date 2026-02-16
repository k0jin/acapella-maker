"""Worker thread for fetching YouTube video title."""

from typing import Optional

from PySide6.QtCore import QThread, Signal

from acapella.gui.workers.base_worker import BaseWorker


class TitleFetchWorker(BaseWorker):
    """Worker thread for fetching a YouTube video title via yt_dlp."""

    finished_ok = Signal(str)

    def __init__(self, url: str, parent: Optional[QThread] = None) -> None:
        super().__init__(parent)
        self.url = url

    def run(self) -> None:
        """Fetch the video title."""
        try:
            import yt_dlp

            ydl_opts = {"quiet": True, "no_warnings": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

            if self._cancelled:
                return

            title = info.get("title", "") if info else ""
            self.finished_ok.emit(title)

        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))
