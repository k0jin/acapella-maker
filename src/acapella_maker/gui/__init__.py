"""GUI application for Acapella Maker."""

import sys


def main():
    """Launch the Acapella Maker GUI application."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from acapella_maker.gui.main_window import MainWindow

    # Enable high-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Acapella Maker")
    app.setOrganizationName("AcapellaMaker")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
