"""Progress section widget for displaying processing progress."""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QElapsedTimer, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from acapella_maker.gui.colors import ColorManager


class ProgressSection(QWidget):
    """Widget for displaying processing progress with cancel button."""

    cancel_requested = Signal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        color_manager: Optional["ColorManager"] = None,
    ) -> None:
        super().__init__(parent)
        self._color_manager = color_manager
        self._elapsed_timer = QElapsedTimer()
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_elapsed)
        self._setup_ui()
        self._connect_signals()
        self.hide()

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        frame.setAutoFillBackground(True)
        # Use panel background color if configured, otherwise use palette-aware styling
        if self._color_manager and self._color_manager.panel_background:
            frame.setStyleSheet(
                f"QFrame {{ background-color: {self._color_manager.panel_background}; }}"
            )
        else:
            frame.setStyleSheet(
                "QFrame { background-color: palette(alternate-base); }"
            )
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(10)
        frame_layout.setContentsMargins(16, 12, 16, 12)

        # Stage label
        self.stage_label = QLabel("Preparing...")
        self.stage_label.setStyleSheet("font-weight: bold;")
        frame_layout.addWidget(self.stage_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        frame_layout.addWidget(self.progress_bar)

        # Bottom row: elapsed time, BPM, and cancel button
        bottom_layout = QHBoxLayout()

        self.elapsed_label = QLabel("Elapsed: 0:00")
        bottom_layout.addWidget(self.elapsed_label)

        self.bpm_label = QLabel("")
        bottom_layout.addWidget(self.bpm_label)

        bottom_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(80)
        bottom_layout.addWidget(self.cancel_btn)

        frame_layout.addLayout(bottom_layout)
        layout.addWidget(frame)

    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        self.cancel_btn.clicked.connect(self._on_cancel)

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Canceling...")
        self.cancel_requested.emit()

    def _update_elapsed(self) -> None:
        """Update the elapsed time display."""
        elapsed_ms = self._elapsed_timer.elapsed()
        seconds = elapsed_ms // 1000
        minutes = seconds // 60
        secs = seconds % 60
        self.elapsed_label.setText(f"Elapsed: {minutes}:{secs:02d}")

    def start(self) -> None:
        """Start progress display."""
        self.stage_label.setText("Preparing...")
        self.progress_bar.setValue(0)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        self._elapsed_timer.start()
        self._update_timer.start(1000)
        self.show()

    def stop(self) -> None:
        """Stop progress display."""
        self._update_timer.stop()

    def reset(self) -> None:
        """Reset and hide progress display."""
        self.stop()
        self.progress_bar.setValue(0)
        self.stage_label.setText("Preparing...")
        self.elapsed_label.setText("Elapsed: 0:00")
        self.bpm_label.setText("")
        self.hide()

    def set_bpm(self, bpm: int) -> None:
        """Update the BPM display label.

        Args:
            bpm: Detected BPM as a whole number.
        """
        self.bpm_label.setText(f"  |  BPM: {bpm}")

    def set_stage(self, stage: str) -> None:
        """Update the current stage label."""
        self.stage_label.setText(stage)

    def set_progress(self, percent: float) -> None:
        """Update the progress bar (0-100)."""
        self.progress_bar.setValue(int(percent))

    def update_progress(self, stage: str, percent: float) -> None:
        """Update both stage and progress."""
        self.set_stage(stage)
        self.set_progress(percent)

    def get_elapsed_seconds(self) -> int:
        """Get elapsed time in seconds."""
        return self._elapsed_timer.elapsed() // 1000
