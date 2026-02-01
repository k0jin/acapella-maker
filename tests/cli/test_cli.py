"""CLI tests using Typer's CliRunner."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from typer.testing import CliRunner

from acapella_maker import __version__
from acapella_maker.cli import app

runner = CliRunner()

# Sample rate for mocks
SAMPLE_RATE = 44100


class TestVersionCommand:
    """Tests for version display."""

    def test_version_flag(self):
        """Test --version flag displays version."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_short_flag(self):
        """Test -V flag displays version."""
        result = runner.invoke(app, ["-V"])

        assert result.exit_code == 0
        assert __version__ in result.stdout


class TestConfigCommand:
    """Tests for config subcommand."""

    def test_config_path(self, temp_config_dir: Path):
        """Test config --path shows config file path."""
        result = runner.invoke(app, ["config", "--path"])

        assert result.exit_code == 0
        assert "config.toml" in result.stdout

    def test_config_show_defaults(self, temp_config_dir: Path):
        """Test config --show displays configuration."""
        result = runner.invoke(app, ["config", "--show"])

        assert result.exit_code == 0
        assert "silence_threshold_db" in result.stdout
        assert "trim_silence" in result.stdout
        assert "Configuration" in result.stdout

    def test_config_init_creates_file(self, temp_config_dir: Path):
        """Test config --init creates config file."""
        config_file = temp_config_dir / "config.toml"
        assert not config_file.exists()

        result = runner.invoke(app, ["config", "--init"])

        assert result.exit_code == 0
        assert "Created config file" in result.stdout
        assert config_file.exists()

    def test_config_init_fails_if_exists(self, temp_config_dir: Path):
        """Test config --init fails if file already exists."""
        config_file = temp_config_dir / "config.toml"
        config_file.write_text("[audio]\n")

        result = runner.invoke(app, ["config", "--init"])

        assert result.exit_code == 1
        assert "already exists" in result.stdout

    def test_config_no_option_shows_help(self, temp_config_dir: Path):
        """Test config without options shows usage message."""
        result = runner.invoke(app, ["config"])

        assert result.exit_code == 0
        assert "--show" in result.stdout or "--init" in result.stdout


class TestBPMCommand:
    """Tests for bpm subcommand."""

    def test_bpm_file_not_found(self, tmp_path: Path):
        """Test bpm command with non-existent file."""
        fake_file = tmp_path / "nonexistent.wav"

        result = runner.invoke(app, ["bpm", str(fake_file)])

        assert result.exit_code == 1
        assert "File not found" in result.stdout or "Error" in result.stdout

    def test_bpm_with_valid_file(self, temp_audio_file: Path):
        """Test bpm command with valid audio file."""
        with patch("acapella_maker.core.pipeline.detect_bpm", return_value=120.0):
            result = runner.invoke(app, ["bpm", str(temp_audio_file)])

        assert result.exit_code == 0
        assert "BPM:" in result.stdout


class TestExtractCommand:
    """Tests for extract subcommand."""

    def test_extract_file_not_found(self, tmp_path: Path):
        """Test extract command with non-existent file."""
        fake_file = tmp_path / "nonexistent.wav"

        result = runner.invoke(app, ["extract", str(fake_file)])

        assert result.exit_code == 1
        assert "File not found" in result.stdout or "Error" in result.stdout

    def test_extract_not_a_file(self, tmp_path: Path):
        """Test extract command with directory instead of file."""
        result = runner.invoke(app, ["extract", str(tmp_path)])

        assert result.exit_code == 1
        assert "Not a file" in result.stdout or "Error" in result.stdout

    def _mock_vocals(self):
        """Create mock vocals data."""
        mock_vocals = np.zeros((2, SAMPLE_RATE), dtype=np.float32)
        t = np.linspace(0, 1.0, SAMPLE_RATE, endpoint=False)
        mock_vocals[0] = (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)
        mock_vocals[1] = mock_vocals[0]
        return mock_vocals, SAMPLE_RATE

    def test_extract_with_valid_file(self, temp_audio_file: Path, tmp_path: Path):
        """Test extract command with valid audio file."""
        output_path = tmp_path / "output.wav"

        with patch("acapella_maker.core.pipeline.detect_bpm", return_value=120.0):
            with patch(
                "acapella_maker.core.pipeline.extract_vocals",
                return_value=self._mock_vocals(),
            ):
                result = runner.invoke(
                    app,
                    ["extract", str(temp_audio_file), "-o", str(output_path)],
                )

        assert result.exit_code == 0
        assert "Done!" in result.stdout
        assert "Output:" in result.stdout
        assert output_path.exists()

    def test_extract_with_no_trim(self, temp_audio_file: Path, tmp_path: Path):
        """Test extract with --no-trim flag."""
        output_path = tmp_path / "output_no_trim.wav"

        with patch("acapella_maker.core.pipeline.detect_bpm", return_value=120.0):
            with patch(
                "acapella_maker.core.pipeline.extract_vocals",
                return_value=self._mock_vocals(),
            ):
                result = runner.invoke(
                    app,
                    [
                        "extract",
                        str(temp_audio_file),
                        "-o",
                        str(output_path),
                        "--no-trim",
                    ],
                )

        assert result.exit_code == 0
        assert output_path.exists()

    def test_extract_with_custom_threshold(self, temp_audio_file: Path, tmp_path: Path):
        """Test extract with custom silence threshold."""
        output_path = tmp_path / "output_custom.wav"

        with patch("acapella_maker.core.pipeline.detect_bpm", return_value=120.0):
            with patch(
                "acapella_maker.core.pipeline.extract_vocals",
                return_value=self._mock_vocals(),
            ):
                result = runner.invoke(
                    app,
                    [
                        "extract",
                        str(temp_audio_file),
                        "-o",
                        str(output_path),
                        "-s",
                        "50",
                    ],
                )

        assert result.exit_code == 0
        assert output_path.exists()


class TestVerboseLogging:
    """Tests for verbose logging flag."""

    def test_verbose_flag_accepted(self, temp_audio_file: Path):
        """Test that --verbose flag is accepted."""
        with patch("acapella_maker.core.pipeline.detect_bpm", return_value=120.0):
            result = runner.invoke(app, ["--verbose", "bpm", str(temp_audio_file)])

        assert result.exit_code == 0
        assert "BPM:" in result.stdout

    def test_verbose_short_flag_accepted(self, temp_audio_file: Path):
        """Test that -v flag is accepted."""
        with patch("acapella_maker.core.pipeline.detect_bpm", return_value=120.0):
            result = runner.invoke(app, ["-v", "bpm", str(temp_audio_file)])

        assert result.exit_code == 0
        assert "BPM:" in result.stdout


class TestHelpText:
    """Tests for help text display."""

    def test_main_help(self):
        """Test main help text."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Extract acapella vocals" in result.stdout
        assert "extract" in result.stdout
        assert "bpm" in result.stdout
        assert "config" in result.stdout

    def test_extract_help(self):
        """Test extract command help."""
        result = runner.invoke(app, ["extract", "--help"])

        assert result.exit_code == 0
        assert "--output" in result.stdout
        assert "--silence-threshold" in result.stdout
        assert "--no-trim" in result.stdout

    def test_bpm_help(self):
        """Test bpm command help."""
        result = runner.invoke(app, ["bpm", "--help"])

        assert result.exit_code == 0
        assert "Detect BPM" in result.stdout

    def test_config_help(self):
        """Test config command help."""
        result = runner.invoke(app, ["config", "--help"])

        assert result.exit_code == 0
        assert "--show" in result.stdout
        assert "--init" in result.stdout
        assert "--path" in result.stdout
