"""Options section widget for processing settings."""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class OptionsSection(QWidget):
    """Widget for configuring processing options."""

    options_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Options")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(12)
        group_layout.setContentsMargins(16, 16, 16, 16)

        # Silence threshold row
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Silence threshold:")
        threshold_label.setMinimumWidth(110)
        threshold_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(30)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(10)

        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 100)
        self.threshold_spin.setValue(30)
        self.threshold_spin.setSuffix(" dB")
        self.threshold_spin.setFixedWidth(80)

        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_slider, 1)
        threshold_layout.addWidget(self.threshold_spin)
        group_layout.addLayout(threshold_layout)

        # Trim silence checkbox
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setContentsMargins(110, 0, 0, 0)
        self.trim_checkbox = QCheckBox("Trim leading silence")
        self.trim_checkbox.setChecked(True)
        self.trim_checkbox.setToolTip(
            "Remove silence from the beginning of the extracted vocals"
        )
        checkbox_layout.addWidget(self.trim_checkbox)
        checkbox_layout.addStretch()
        group_layout.addLayout(checkbox_layout)

        layout.addWidget(group)

    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        self.threshold_slider.valueChanged.connect(self._on_slider_changed)
        self.threshold_spin.valueChanged.connect(self._on_spin_changed)
        self.trim_checkbox.stateChanged.connect(lambda: self.options_changed.emit())

    def _on_slider_changed(self, value: int) -> None:
        """Handle slider value change."""
        self.threshold_spin.blockSignals(True)
        self.threshold_spin.setValue(value)
        self.threshold_spin.blockSignals(False)
        self.options_changed.emit()

    def _on_spin_changed(self, value: int) -> None:
        """Handle spin box value change."""
        self.threshold_slider.blockSignals(True)
        self.threshold_slider.setValue(value)
        self.threshold_slider.blockSignals(False)
        self.options_changed.emit()

    def get_silence_threshold(self) -> float:
        """Get the silence threshold in dB."""
        return float(self.threshold_slider.value())

    def get_trim_silence(self) -> bool:
        """Get whether to trim leading silence."""
        return self.trim_checkbox.isChecked()

    def set_enabled(self, enabled: bool):
        """Enable or disable all controls."""
        self.threshold_slider.setEnabled(enabled)
        self.threshold_spin.setEnabled(enabled)
        self.trim_checkbox.setEnabled(enabled)

    def set_silence_threshold(self, value: float) -> None:
        """Set the silence threshold value.

        Args:
            value: Threshold in dB (0-100).
        """
        int_value = int(value)
        self.threshold_slider.setValue(int_value)
        self.threshold_spin.setValue(int_value)

    def set_trim_silence(self, enabled: bool) -> None:
        """Set whether to trim leading silence.

        Args:
            enabled: True to enable trimming.
        """
        self.trim_checkbox.setChecked(enabled)
