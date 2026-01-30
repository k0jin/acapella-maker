"""Color management for the GUI."""

from acapella_maker.config import ColorsConfig


class ColorManager:
    """Manages UI colors from configuration."""

    def __init__(self, colors_config: ColorsConfig) -> None:
        """Initialize ColorManager with a ColorsConfig.

        Args:
            colors_config: The colors configuration to use.
        """
        self._config = colors_config

    @property
    def success(self) -> str:
        """Get the success color (positive states, completion)."""
        return self._config.success

    @property
    def error(self) -> str:
        """Get the error color (error states, invalid input)."""
        return self._config.error

    @property
    def accent(self) -> str:
        """Get the accent color (primary action color)."""
        return self._config.accent

    @property
    def surface(self) -> str:
        """Get the surface color (elevated backgrounds).

        Returns empty string if not set, meaning system default should be used.
        """
        return self._config.surface


def build_stylesheet(color_manager: ColorManager) -> str:
    """Generate a global QSS stylesheet from color configuration.

    Args:
        color_manager: ColorManager instance with color values.

    Returns:
        QSS stylesheet string to apply globally.
    """
    rules = []

    # Progress bar accent color
    if color_manager.accent:
        rules.append(f"""
QProgressBar::chunk {{
    background-color: {color_manager.accent};
}}
""")

    # Button accent styling (for default buttons)
    if color_manager.accent:
        rules.append(f"""
QPushButton[default="true"] {{
    background-color: {color_manager.accent};
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
}}
QPushButton[default="true"]:hover {{
    background-color: {color_manager.accent};
    opacity: 0.9;
}}
QPushButton[default="true"]:disabled {{
    background-color: #cccccc;
    color: #888888;
}}
""")

    return "\n".join(rules)
