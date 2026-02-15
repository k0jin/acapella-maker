"""Input section widget for file path and YouTube URL."""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
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

from acapella.core.youtube import is_youtube_url

if TYPE_CHECKING:
    from acapella.gui.colors import ColorManager


class InputSection(QWidget):
    """Widget for selecting input file or YouTube URL."""

    input_changed = Signal(str)  # Emitted when valid input is set

    AUDIO_FILTERS = "Audio Files (*.wav *.mp3 *.flac *.ogg *.m4a *.aac);;All Files (*)"

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        color_manager: Optional["ColorManager"] = None,
    ) -> None:
        super().__init__(parent)
        self._color_manager = color_manager
        self._setup_ui()
        self._connect_signals()
        self.setAcceptDrops(True)

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Input")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(12)
        group_layout.setContentsMargins(16, 16, 16, 16)

        # File input row
        file_layout = QHBoxLayout()
        file_label = QLabel("File:")
        file_label.setFixedWidth(80)
        file_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Select an audio file or drag and drop...")
        self.browse_btn = QPushButton("Browse...")
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_edit, 1)
        file_layout.addWidget(self.browse_btn)
        group_layout.addLayout(file_layout)

        # Separator
        separator_layout = QHBoxLayout()
        separator_label = QLabel("— or —")
        separator_layout.addStretch()
        separator_layout.addWidget(separator_label)
        separator_layout.addStretch()
        group_layout.addLayout(separator_layout)

        # YouTube URL row
        url_layout = QHBoxLayout()
        url_label = QLabel("YouTube:")
        url_label.setFixedWidth(80)
        url_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Paste a YouTube URL...")
        self.url_status = QLabel()
        self.url_status.setFixedWidth(24)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit, 1)
        url_layout.addWidget(self.url_status)
        group_layout.addLayout(url_layout)

        layout.addWidget(group)

    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        self.browse_btn.clicked.connect(self._on_browse)
        self.file_edit.textChanged.connect(self._on_file_changed)
        self.url_edit.textChanged.connect(self._on_url_changed)

    def _on_browse(self) -> None:
        """Handle browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            str(Path.home()),
            self.AUDIO_FILTERS,
        )
        if file_path:
            self.file_edit.setText(file_path)
            self.url_edit.clear()

    def _on_file_changed(self, text: str) -> None:
        """Handle file path text change."""
        if text and Path(text).is_file():
            self.url_edit.clear()
            self.input_changed.emit(text)

    def _on_url_changed(self, text: str) -> None:
        """Handle YouTube URL text change."""
        if not text:
            self.url_status.setText("")
            return

        if is_youtube_url(text):
            self.url_status.setText("✓")
            valid_color = (
                self._color_manager.valid_input if self._color_manager else "#2e7d32"
            )
            self.url_status.setStyleSheet(f"color: {valid_color}; font-weight: bold;")
            self.file_edit.clear()
            self.input_changed.emit(text)
        else:
            self.url_status.setText("✗")
            invalid_color = (
                self._color_manager.invalid_input if self._color_manager else "#c62828"
            )
            self.url_status.setStyleSheet(f"color: {invalid_color}; font-weight: bold;")

    def get_input(self) -> str:
        """Get the current input (file path or YouTube URL)."""
        if self.url_edit.text() and is_youtube_url(self.url_edit.text()):
            return self.url_edit.text()
        return self.file_edit.text()

    def is_youtube(self) -> bool:
        """Check if current input is a YouTube URL."""
        return bool(self.url_edit.text() and is_youtube_url(self.url_edit.text()))

    def is_valid(self) -> bool:
        """Check if there is valid input."""
        if self.is_youtube():
            return True
        file_path = self.file_edit.text()
        return bool(file_path and Path(file_path).is_file())

    def get_input_name(self) -> str:
        """Get a display name for the input (filename or 'YouTube video')."""
        if self.is_youtube():
            return "YouTube video"
        file_path = self.file_edit.text()
        if file_path:
            return Path(file_path).stem
        return ""

    def clear(self):
        """Clear all inputs."""
        self.file_edit.clear()
        self.url_edit.clear()
        self.url_status.clear()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event for file drops."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event for file drops."""
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            self.file_edit.setText(file_path)
            self.url_edit.clear()
