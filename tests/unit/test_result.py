"""Unit tests for result data classes."""

from pathlib import Path

import pytest

from acapella_maker.models.result import ProcessingOptions, ProcessingResult


class TestProcessingOptions:
    """Tests for ProcessingOptions dataclass."""

    def test_default_values(self):
        """Test default option values."""
        options = ProcessingOptions()

        assert options.silence_threshold_db == 30.0
        assert options.trim_silence is True
        assert options.fade_in_ms == 5.0
        assert options.buffer_before_ms == 10.0
        assert options.pre_detected_bpm is None
        assert options.progress_callback is None

    def test_custom_values(self):
        """Test creating options with custom values."""
        options = ProcessingOptions(
            silence_threshold_db=40.0,
            trim_silence=False,
            fade_in_ms=10.0,
            buffer_before_ms=20.0,
            pre_detected_bpm=120.0,
        )

        assert options.silence_threshold_db == 40.0
        assert options.trim_silence is False
        assert options.fade_in_ms == 10.0
        assert options.buffer_before_ms == 20.0
        assert options.pre_detected_bpm == 120.0

    def test_progress_callback(self):
        """Test progress callback option."""
        callback_calls = []

        def callback(stage: str, percent: float):
            callback_calls.append((stage, percent))

        options = ProcessingOptions(progress_callback=callback)

        # Simulate calling the callback
        options.progress_callback("Test", 50.0)

        assert len(callback_calls) == 1
        assert callback_calls[0] == ("Test", 50.0)


class TestProcessingResult:
    """Tests for ProcessingResult dataclass."""

    @pytest.fixture
    def sample_result(self, tmp_path: Path) -> ProcessingResult:
        """Create a sample processing result."""
        return ProcessingResult(
            input_path=tmp_path / "input.wav",
            output_path=tmp_path / "output.wav",
            bpm=120.0,
            original_duration=10.0,
            trimmed_duration=9.5,
            silence_trimmed_ms=500.0,
            sample_rate=44100,
        )

    def test_result_stores_all_fields(
        self, sample_result: ProcessingResult, tmp_path: Path
    ):
        """Test that all fields are stored correctly."""
        assert sample_result.input_path == tmp_path / "input.wav"
        assert sample_result.output_path == tmp_path / "output.wav"
        assert sample_result.bpm == 120.0
        assert sample_result.original_duration == 10.0
        assert sample_result.trimmed_duration == 9.5
        assert sample_result.silence_trimmed_ms == 500.0
        assert sample_result.sample_rate == 44100

    def test_duration_change_property(self, sample_result: ProcessingResult):
        """Test duration_change property calculation."""
        # trimmed_duration - original_duration = 9.5 - 10.0 = -0.5
        assert sample_result.duration_change == -0.5

    def test_duration_change_no_trimming(self, tmp_path: Path):
        """Test duration_change when no trimming occurred."""
        result = ProcessingResult(
            input_path=tmp_path / "input.wav",
            output_path=tmp_path / "output.wav",
            bpm=120.0,
            original_duration=10.0,
            trimmed_duration=10.0,
            silence_trimmed_ms=0.0,
            sample_rate=44100,
        )

        assert result.duration_change == 0.0

    def test_duration_change_positive(self, tmp_path: Path):
        """Test duration_change can be positive (though unusual)."""
        # This would be unusual but the property should handle it
        result = ProcessingResult(
            input_path=tmp_path / "input.wav",
            output_path=tmp_path / "output.wav",
            bpm=120.0,
            original_duration=10.0,
            trimmed_duration=11.0,  # Longer than original
            silence_trimmed_ms=0.0,
            sample_rate=44100,
        )

        assert result.duration_change == 1.0

    def test_paths_are_path_objects(self, sample_result: ProcessingResult):
        """Test that input and output paths are Path objects."""
        assert isinstance(sample_result.input_path, Path)
        assert isinstance(sample_result.output_path, Path)
