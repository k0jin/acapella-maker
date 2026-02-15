"""GUI application for Acapella."""

import sys


def main():
    """Launch the Acapella GUI application."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from acapella.config import get_config
    from acapella.gui.colors import ColorManager, build_stylesheet
    from acapella.gui.main_window import MainWindow

    # Enable high-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Acapella")
    app.setOrganizationName("Acapella")

    # Set up color manager and apply global stylesheet
    config = get_config()
    color_manager = ColorManager(config.colors)
    stylesheet = build_stylesheet(color_manager)
    if stylesheet:
        app.setStyleSheet(stylesheet)

    window = MainWindow(color_manager=color_manager)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
