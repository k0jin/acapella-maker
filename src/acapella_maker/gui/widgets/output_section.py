"""Output section widget for output path selection."""

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class OutputSection(QWidget):
    """Widget for selecting output file path."""

    output_changed = Signal(str)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        default_dir_getter: Optional[Callable[[], Path]] = None,
    ) -> None:
        super().__init__(parent)
        self._default_dir_getter = default_dir_getter
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Output")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(12)
        group_layout.setContentsMargins(16, 16, 16, 16)

        output_layout = QHBoxLayout()
        output_label = QLabel("Save to:")
        output_label.setFixedWidth(80)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Output file path...")
        self.browse_btn = QPushButton("Browse...")
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_edit, 1)
        output_layout.addWidget(self.browse_btn)
        group_layout.addLayout(output_layout)

        layout.addWidget(group)

    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        self.browse_btn.clicked.connect(self._on_browse)
        self.output_edit.textChanged.connect(self.output_changed.emit)

    def _on_browse(self) -> None:
        """Handle browse button click."""
        current = self.output_edit.text()
        start_dir = str(Path(current).parent) if current else str(self._default_dir())

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Acapella As",
            start_dir,
            "WAV Files (*.wav);;All Files (*)",
        )
        if file_path:
            if not file_path.endswith(".wav"):
                file_path += ".wav"
            self.output_edit.setText(file_path)

    def _default_dir(self) -> Path:
        """Get default output directory from config or fallback."""
        if self._default_dir_getter:
            return self._default_dir_getter()
        downloads = Path.home() / "Downloads"
        if downloads.exists():
            return downloads
        return Path.home()

    def set_from_input(self, input_path: str, is_youtube: bool = False):
        """Auto-populate output path based on input.

        Args:
            input_path: The input file path or YouTube URL.
            is_youtube: Whether the input is a YouTube URL.
        """
        if is_youtube:
            # For YouTube, use generic name in Downloads
            output_path = self._default_dir() / "youtube_acapella.wav"
        else:
            # For local files, use same directory with _acapella suffix
            input_p = Path(input_path)
            output_path = input_p.parent / f"{input_p.stem}_acapella.wav"

        self.output_edit.setText(str(output_path))

    def get_output_path(self) -> str:
        """Get the output file path."""
        return self.output_edit.text()

    def is_valid(self) -> bool:
        """Check if output path is valid."""
        path = self.output_edit.text()
        if not path:
            return False
        # Check parent directory exists
        parent = Path(path).parent
        return parent.exists()

    def clear(self):
        """Clear the output path."""
        self.output_edit.clear()

    def set_enabled(self, enabled: bool):
        """Enable or disable controls."""
        self.output_edit.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)
