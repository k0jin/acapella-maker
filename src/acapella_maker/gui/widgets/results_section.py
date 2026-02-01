"""Results section widget for displaying processing results."""

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from acapella_maker.models.result import ProcessingResult

if TYPE_CHECKING:
    from acapella_maker.gui.colors import ColorManager


class ResultsSection(QWidget):
    """Widget for displaying processing results."""

    process_another = Signal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        color_manager: Optional["ColorManager"] = None,
    ) -> None:
        super().__init__(parent)
        self._output_path: str = ""
        self._color_manager = color_manager
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
            frame.setStyleSheet("QFrame { background-color: palette(alternate-base); }")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(10)
        frame_layout.setContentsMargins(16, 12, 16, 12)

        # Success header
        success_color = (
            self._color_manager.valid_input if self._color_manager else "#2e7d32"
        )
        header = QLabel("Processing Complete!")
        header.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {success_color};"
        )
        frame_layout.addWidget(header)

        # Results grid
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.setHorizontalSpacing(12)

        self.output_label = QLabel()
        self.output_label.setWordWrap(True)
        grid.addWidget(QLabel("Output:"), 0, 0)
        grid.addWidget(self.output_label, 0, 1)

        self.bpm_label = QLabel()
        grid.addWidget(QLabel("BPM:"), 1, 0)
        grid.addWidget(self.bpm_label, 1, 1)

        self.duration_label = QLabel()
        grid.addWidget(QLabel("Duration:"), 2, 0)
        grid.addWidget(self.duration_label, 2, 1)

        self.trimmed_label = QLabel()
        grid.addWidget(QLabel("Silence trimmed:"), 3, 0)
        grid.addWidget(self.trimmed_label, 3, 1)

        frame_layout.addLayout(grid)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.setFixedWidth(100)
        btn_layout.addWidget(self.open_folder_btn)

        self.another_btn = QPushButton("Process Another")
        self.another_btn.setFixedWidth(120)
        btn_layout.addWidget(self.another_btn)

        frame_layout.addLayout(btn_layout)
        layout.addWidget(frame)

    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        self.open_folder_btn.clicked.connect(self._on_open_folder)
        self.another_btn.clicked.connect(self._on_process_another)

    def _on_open_folder(self) -> None:
        """Open the output folder in the system file manager."""
        if not self._output_path:
            return

        path = Path(self._output_path)
        folder = path.parent if path.is_file() else path

        # Validate folder exists before opening
        if not folder.exists():
            return

        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            elif sys.platform == "win32":
                subprocess.run(["explorer", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except OSError:
            # Silently fail if file manager cannot be opened
            pass

    def _on_process_another(self) -> None:
        """Handle process another button click."""
        self.hide()
        self.process_another.emit()

    def show_result(self, result: ProcessingResult):
        """Display processing result.

        Args:
            result: The ProcessingResult from the pipeline.
        """
        self._output_path = str(result.output_path)

        self.output_label.setText(str(result.output_path))
        self.bpm_label.setText(f"{result.bpm:.1f}")

        # Format duration as mm:ss
        minutes = int(result.trimmed_duration // 60)
        seconds = int(result.trimmed_duration % 60)
        self.duration_label.setText(f"{minutes}:{seconds:02d}")

        if result.silence_trimmed_ms > 0:
            self.trimmed_label.setText(f"{result.silence_trimmed_ms:.0f} ms")
        else:
            self.trimmed_label.setText("None")

        self.show()

    def show_bpm_result(self, bpm: float, input_name: str):
        """Display BPM-only result.

        Args:
            bpm: Detected BPM value.
            input_name: Name of the input file/source.
        """
        self._output_path = ""

        self.output_label.setText(f"(BPM detection only for: {input_name})")
        self.bpm_label.setText(f"{bpm:.1f}")
        self.duration_label.setText("N/A")
        self.trimmed_label.setText("N/A")
        self.open_folder_btn.setEnabled(False)

        self.show()

    def reset(self) -> None:
        """Reset and hide the results section."""
        self._output_path = ""
        self.open_folder_btn.setEnabled(True)
        self.hide()
