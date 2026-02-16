"""Main application window for Acapella GUI."""

from pathlib import Path
from typing import Callable, Optional, Union

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from acapella.config import get_config
from acapella.gui.colors import ColorManager
from acapella.gui.widgets import (
    InputSection,
    OptionsSection,
    OutputSection,
    ProgressSection,
    ResultsSection,
)
from acapella.gui.workers import BaseWorker, BPMWorker, DownloadWorker, ExtractionWorker
from acapella.models.result import ProcessingResult


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        color_manager: Optional[ColorManager] = None,
    ) -> None:
        super().__init__(parent)
        self._worker: Optional[Union[ExtractionWorker, BPMWorker, DownloadWorker]] = None
        self._config = get_config()
        self._color_manager = color_manager
        self._setup_ui()
        self._connect_signals()
        self._apply_config()
        self._update_button_state()

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        self.setWindowTitle("Acapella")
        self.setMinimumSize(
            self._config.window.min_width, self._config.window.min_height
        )
        self.resize(
            self._config.window.default_width, self._config.window.default_height
        )

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Input section
        self.input_section = InputSection(color_manager=self._color_manager)
        layout.addWidget(self.input_section)

        # Options section
        self.options_section = OptionsSection()
        layout.addWidget(self.options_section)

        # Output section (pass config-based default directory getter)
        self.output_section = OutputSection(
            default_dir_getter=lambda: self._config.output.get_default_directory()
        )
        layout.addWidget(self.output_section)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.download_btn = QPushButton("Download")
        self.download_btn.setFixedWidth(130)
        btn_layout.addWidget(self.download_btn)
        btn_layout.addStretch()

        self.bpm_btn = QPushButton("Detect BPM Only")
        self.bpm_btn.setFixedWidth(130)
        btn_layout.addWidget(self.bpm_btn)
        btn_layout.addStretch()

        self.extract_btn = QPushButton("Extract Acapella")
        self.extract_btn.setFixedWidth(130)
        self.extract_btn.setDefault(True)
        btn_layout.addWidget(self.extract_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Progress section (hidden by default)
        self.progress_section = ProgressSection(color_manager=self._color_manager)
        layout.addWidget(self.progress_section)

        # Results section (hidden by default)
        self.results_section = ResultsSection(color_manager=self._color_manager)
        layout.addWidget(self.results_section)

        layout.addStretch()

    def _apply_config(self) -> None:
        """Apply configuration values to UI widgets."""
        self.options_section.set_silence_threshold(
            self._config.audio.silence_threshold_db
        )
        self.options_section.set_trim_silence(self._config.audio.trim_silence)

    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        # Input changes
        self.input_section.input_changed.connect(self._on_input_changed)

        # Action buttons
        self.download_btn.clicked.connect(self._on_download)
        self.extract_btn.clicked.connect(self._on_extract)
        self.bpm_btn.clicked.connect(self._on_bpm_only)

        # Progress
        self.progress_section.cancel_requested.connect(self._on_cancel)

        # Results
        self.results_section.process_another.connect(self._on_process_another)

    def _update_button_state(self) -> None:
        """Update button enabled state based on input validity."""
        has_valid_input = self.input_section.is_valid()
        has_valid_output = self.output_section.is_valid()
        is_youtube = self.input_section.is_youtube()
        is_processing = self._worker is not None and self._worker.isRunning()

        self.download_btn.setEnabled(
            has_valid_input and is_youtube and has_valid_output and not is_processing
        )
        self.extract_btn.setEnabled(
            has_valid_input and has_valid_output and not is_processing
        )
        self.bpm_btn.setEnabled(has_valid_input and not is_processing)

    def _on_input_changed(self, input_path: str) -> None:
        """Handle input path change."""
        is_youtube = self.input_section.is_youtube()
        self.output_section.set_from_input(input_path, is_youtube)
        self._update_button_state()

    def _connect_worker_signals(
        self, worker: BaseWorker, on_finished: Callable
    ) -> None:
        """Connect common worker signals."""
        worker.stage_changed.connect(self.progress_section.set_stage)
        worker.progress.connect(self.progress_section.update_progress)
        worker.finished_ok.connect(on_finished)
        worker.error.connect(self._on_error)
        worker.finished.connect(self._on_worker_done)

    def _on_extract(self) -> None:
        """Start acapella extraction."""
        if not self._validate_inputs():
            return

        self.results_section.hide()
        self._set_processing_state(True)

        self._worker = ExtractionWorker(
            input_path=self.input_section.get_input(),
            output_path=self.output_section.get_output_path(),
            silence_threshold=self.options_section.get_silence_threshold(),
            trim_silence=self.options_section.get_trim_silence(),
            parent=self,
        )
        self._worker.bpm_detected.connect(self.progress_section.set_bpm)
        self._connect_worker_signals(self._worker, self._on_extraction_finished)
        self._worker.start()

    def _on_bpm_only(self) -> None:
        """Start BPM-only detection."""
        if not self.input_section.is_valid():
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please select a valid audio file or YouTube URL.",
            )
            return

        self.results_section.hide()
        self._set_processing_state(True)

        self._worker = BPMWorker(
            input_path=self.input_section.get_input(),
            parent=self,
        )
        self._worker.bpm_detected.connect(self.progress_section.set_bpm)
        self._connect_worker_signals(self._worker, self._on_bpm_finished)
        self._worker.start()

    def _on_download(self) -> None:
        """Start YouTube audio download."""
        if not self._validate_inputs():
            return

        self.results_section.hide()
        self._set_processing_state(True)

        output_dir = Path(self.output_section.get_output_path()).parent

        self._worker = DownloadWorker(
            url=self.input_section.get_input(),
            output_dir=output_dir,
            parent=self,
        )
        self._connect_worker_signals(self._worker, self._on_download_finished)
        self._worker.start()

    def _on_download_finished(self, output_path: str) -> None:
        """Handle successful download."""
        self.progress_section.reset()
        self.results_section.show_download_result(output_path)

    def _validate_inputs(self) -> bool:
        """Validate inputs before processing.

        Returns:
            True if all inputs are valid, False otherwise.
        """
        if not self.input_section.is_valid():
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please select a valid audio file or YouTube URL.",
            )
            return False

        if not self.output_section.is_valid():
            QMessageBox.warning(
                self,
                "Invalid Output",
                "Please specify a valid output path. The parent directory must exist.",
            )
            return False

        return True

    def _set_processing_state(self, processing: bool) -> None:
        """Enable/disable UI during processing."""
        self.input_section.setEnabled(not processing)
        self.options_section.set_enabled(not processing)
        self.output_section.set_enabled(not processing)
        self.download_btn.setEnabled(not processing)
        self.extract_btn.setEnabled(not processing)
        self.bpm_btn.setEnabled(not processing)

        if processing:
            self.progress_section.start()
        else:
            self.progress_section.stop()

    def _on_cancel(self) -> None:
        """Handle cancel request."""
        if self._worker:
            self._worker.cancel()

    def _on_extraction_finished(self, result: ProcessingResult) -> None:
        """Handle successful extraction."""
        self.progress_section.reset()
        self.results_section.show_result(result)

    def _on_bpm_finished(self, bpm: float) -> None:
        """Handle successful BPM detection."""
        self.progress_section.reset()
        self.results_section.show_bpm_result(bpm, self.input_section.get_input_name())

    def _on_error(self, message: str) -> None:
        """Handle processing error."""
        self.progress_section.reset()
        QMessageBox.critical(
            self, "Processing Error", f"An error occurred:\n\n{message}"
        )

    def _on_worker_done(self) -> None:
        """Handle worker thread completion."""
        self._set_processing_state(False)
        self._worker = None
        self._update_button_state()

    def _on_process_another(self) -> None:
        """Reset form for another processing run."""
        self.input_section.clear()
        self.output_section.clear()
        self.results_section.reset()
        self._update_button_state()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close."""
        if self._worker and self._worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Processing in Progress",
                "Processing is still in progress. Are you sure you want to quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            self._worker.cancel()
            self._worker.wait(5000)  # Wait up to 5 seconds

        event.accept()
