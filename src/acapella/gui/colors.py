"""Color management for the GUI."""

from acapella.config import ColorsConfig


class ColorManager:
    """Manages UI colors from configuration."""

    def __init__(self, colors_config: ColorsConfig) -> None:
        """Initialize ColorManager with a ColorsConfig.

        Args:
            colors_config: The colors configuration to use.
        """
        self._config = colors_config

    @property
    def valid_input(self) -> str:
        """Get the valid input color (checkmark for valid YouTube URL)."""
        return self._config.valid_input

    @property
    def invalid_input(self) -> str:
        """Get the invalid input color (X mark for invalid input)."""
        return self._config.invalid_input

    @property
    def progress_bar(self) -> str:
        """Get the progress bar color (progress bar chunk)."""
        return self._config.progress_bar

    @property
    def panel_background(self) -> str:
        """Get the panel background color (QGroupBox/QFrame backgrounds).

        Returns empty string if not set, meaning system default should be used.
        """
        return self._config.panel_background

    @property
    def window_background(self) -> str:
        """Get the window background color (main window background).

        Returns empty string if not set, meaning system default should be used.
        """
        return self._config.window_background

    @property
    def button_background(self) -> str:
        """Get the button background color.

        Returns empty string if not set, meaning system default should be used.
        """
        return self._config.button_background

    @property
    def header_text(self) -> str:
        """Get the section header text color."""
        return self._config.header_text

    @property
    def panel_text(self) -> str:
        """Get the in-panel text color."""
        return self._config.panel_text


def build_stylesheet(color_manager: ColorManager) -> str:
    """Generate a global QSS stylesheet from color configuration.

    Args:
        color_manager: ColorManager instance with color values.

    Returns:
        QSS stylesheet string to apply globally.
    """
    rules = []

    # Main window background color
    if color_manager.window_background:
        rules.append(f"""
QMainWindow, QMainWindow > QWidget {{
    background-color: {color_manager.window_background};
}}
""")

    # Button background color
    if color_manager.button_background:
        rules.append(f"""
QPushButton {{
    background-color: {color_manager.button_background};
}}
""")

    # Progress bar color
    if color_manager.progress_bar:
        rules.append(f"""
QProgressBar::chunk {{
    background-color: {color_manager.progress_bar};
}}
""")

    # Panel background color for group boxes and frames
    if color_manager.panel_background:
        surface_style = f"background-color: {color_manager.panel_background};"
    else:
        surface_style = "background-color: palette(alternate-base);"

    # Header text color (section titles like "Input", "Options", "Output")
    if color_manager.header_text:
        title_color = f"color: {color_manager.header_text};"
    else:
        title_color = ""

    # Panel text color (labels inside panels)
    if color_manager.panel_text:
        panel_text_style = f"color: {color_manager.panel_text};"
    else:
        panel_text_style = ""

    rules.append(f"""
QGroupBox {{
    {surface_style}
    border-radius: 6px;
    margin-top: 24px;
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 0px;
    top: 0px;
    padding: 0 0 4px 0;
    font-weight: bold;
    {title_color}
}}
QGroupBox QLabel {{
    {panel_text_style}
}}
""")

    return "\n".join(rules)
