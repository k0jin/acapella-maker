"""Configuration management for Acapella Maker."""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Import tomli for Python < 3.11, otherwise use stdlib tomllib
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

APP_NAME = "acapella-maker"
CONFIG_FILENAME = "config.toml"


def get_config_dir() -> Path:
    """Get the platform-specific configuration directory.

    Returns:
        Path to config directory:
        - Linux/macOS: ~/.config/acapella-maker/
        - Windows: %APPDATA%/acapella-maker/
    """
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Roaming"
    else:
        # Linux and macOS
        base = Path.home() / ".config"
    return base / APP_NAME


def get_config_path() -> Path:
    """Get the full path to the configuration file."""
    return get_config_dir() / CONFIG_FILENAME


@dataclass
class WindowConfig:
    """Window dimension configuration."""

    min_width: int = 520
    min_height: int = 680
    default_width: int = 520
    default_height: int = 680


@dataclass
class AudioConfig:
    """Audio processing configuration."""

    silence_threshold_db: float = 30.0
    trim_silence: bool = True
    fade_in_ms: float = 5.0
    buffer_before_ms: float = 10.0


@dataclass
class OutputConfig:
    """Output configuration."""

    default_directory: Optional[str] = None  # None = ~/Downloads
    filename_template: str = "{stem}_acapella_{bpm}bpm"

    def get_default_directory(self) -> Path:
        """Get the resolved default output directory."""
        if self.default_directory:
            return Path(self.default_directory).expanduser()
        downloads = Path.home() / "Downloads"
        return downloads if downloads.exists() else Path.cwd()


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    file: Optional[str] = None


@dataclass
class Config:
    """Application configuration."""

    audio: AudioConfig = field(default_factory=AudioConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    window: WindowConfig = field(default_factory=WindowConfig)

    def to_dict(self) -> dict:
        """Convert config to dictionary for TOML serialization."""
        result = {
            "audio": {
                "silence_threshold_db": self.audio.silence_threshold_db,
                "trim_silence": self.audio.trim_silence,
                "fade_in_ms": self.audio.fade_in_ms,
                "buffer_before_ms": self.audio.buffer_before_ms,
            },
            "output": {
                "filename_template": self.output.filename_template,
            },
            "logging": {
                "level": self.logging.level,
            },
            "window": {
                "min_width": self.window.min_width,
                "min_height": self.window.min_height,
                "default_width": self.window.default_width,
                "default_height": self.window.default_height,
            },
        }
        # Only include optional values if they're set (TOML doesn't support None)
        if self.output.default_directory is not None:
            result["output"]["default_directory"] = self.output.default_directory
        if self.logging.file is not None:
            result["logging"]["file"] = self.logging.file
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create Config from dictionary."""
        audio_data = data.get("audio", {})
        output_data = data.get("output", {})
        logging_data = data.get("logging", {})
        window_data = data.get("window", {})

        return cls(
            audio=AudioConfig(
                silence_threshold_db=audio_data.get("silence_threshold_db", 30.0),
                trim_silence=audio_data.get("trim_silence", True),
                fade_in_ms=audio_data.get("fade_in_ms", 5.0),
                buffer_before_ms=audio_data.get("buffer_before_ms", 10.0),
            ),
            output=OutputConfig(
                default_directory=output_data.get("default_directory"),
                filename_template=output_data.get(
                    "filename_template", "{stem}_acapella_{bpm}bpm"
                ),
            ),
            logging=LoggingConfig(
                level=logging_data.get("level", "INFO"),
                file=logging_data.get("file"),
            ),
            window=WindowConfig(
                min_width=window_data.get("min_width", 520),
                min_height=window_data.get("min_height", 680),
                default_width=window_data.get("default_width", 520),
                default_height=window_data.get("default_height", 680),
            ),
        )


def load_config() -> Config:
    """Load configuration from file.

    Returns:
        Config object with values from file, or defaults if file doesn't exist.
    """
    config_path = get_config_path()

    if not config_path.exists():
        return Config()

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        return Config.from_dict(data)
    except Exception:
        # Return defaults if config file is invalid
        return Config()


def save_config(config: Config) -> None:
    """Save configuration to file.

    Args:
        config: Config object to save.
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "wb") as f:
        tomli_w.dump(config.to_dict(), f)


def init_config() -> Path:
    """Initialize configuration file with defaults.

    Returns:
        Path to the created config file.
    """
    config = Config()
    save_config(config)
    return get_config_path()


# Module-level cached config
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the cached configuration, loading from file if needed.

    Returns:
        Cached Config object.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> Config:
    """Reload configuration from file.

    Returns:
        Fresh Config object.
    """
    global _config
    _config = load_config()
    return _config
