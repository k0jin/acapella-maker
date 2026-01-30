"""Base worker class for background threads."""

from typing import Optional

from PySide6.QtCore import QThread, Signal


class BaseWorker(QThread):
    """Base class for worker threads with common signals and cancellation."""

    stage_changed = Signal(str)
    progress = Signal(str, float)
    error = Signal(str)

    def __init__(self, parent: Optional[QThread] = None) -> None:
        super().__init__(parent)
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the worker."""
        self._cancelled = True
