"""Integration tests for the processing pipeline with mocked Demucs."""

from pathlib import Path

import numpy as np
import pytest

from acapella.core.pipeline import AcapellaPipeline
from acapella.models.result import ProcessingOptions, ProcessingResult


class TestAcapellaPipeline:
    """Integration tests for AcapellaPipeline."""

    def test_pipeline_process_with_defaults(
        self,
        mock_extract_vocals,
        mock_pipeline_bpm,
        temp_audio_file: Path,
        tmp_path: Path,
    ):
        """Test full pipeline processing with default options."""
        output_path = tmp_path / "output_acapella.wav"
        pipeline = AcapellaPipeline()

        result = pipeline.process(temp_audio_file, output_path)

        assert isinstance(result, ProcessingResult)
        assert result.input_path == temp_audio_file
        assert result.output_path == output_path
        assert output_path.exists()
        assert result.bpm > 0
        assert result.sample_rate == 44100

        # Verify mock was called
        mock_extract_vocals.assert_called_once()

    def test_pipeline_process_without_trimming(
        self,
        mock_extract_vocals,
        mock_pipeline_bpm,
        temp_audio_file: Path,
        tmp_path: Path,
    ):
        """Test pipeline with silence trimming disabled."""
        output_path = tmp_path / "output_no_trim.wav"
        options = ProcessingOptions(trim_silence=False)
        pipeline = AcapellaPipeline(options)

        result = pipeline.process(temp_audio_file, output_path)

        assert result.silence_trimmed_ms == 0.0
        assert output_path.exists()

    def test_pipeline_process_with_custom_threshold(
        self,
        mock_extract_vocals,
        mock_pipeline_bpm,
        temp_audio_file: Path,
        tmp_path: Path,
    ):
        """Test pipeline with custom silence threshold."""
        output_path = tmp_path / "output_custom.wav"
        options = ProcessingOptions(
            silence_threshold_db=50.0,
            trim_silence=True,
        )
        pipeline = AcapellaPipeline(options)

        result = pipeline.process(temp_audio_file, output_path)

        assert output_path.exists()
        assert isinstance(result, ProcessingResult)

    def test_pipeline_generates_default_output_path(
        self,
        mock_extract_vocals,
        mock_pipeline_bpm,
        temp_audio_file: Path,
    ):
        """Test that pipeline generates default output path when not provided."""
        pipeline = AcapellaPipeline()

        result = pipeline.process(temp_audio_file)

        expected_output = (
            temp_audio_file.parent / f"{temp_audio_file.stem}_acapella.wav"
        )
        assert result.output_path == expected_output
        assert expected_output.exists()

        # Cleanup
        expected_output.unlink()

    def test_pipeline_with_pre_detected_bpm(
        self,
        mock_extract_vocals,
        temp_audio_file: Path,
        tmp_path: Path,
        mocker,
    ):
        """Test pipeline skips BPM detection when pre-detected."""
        output_path = tmp_path / "output_predetected.wav"
        options = ProcessingOptions(pre_detected_bpm=125.0)
        pipeline = AcapellaPipeline(options)

        # Mock BPM detection to verify it's not called
        mock_detect = mocker.patch("acapella.core.pipeline.detect_bpm")

        result = pipeline.process(temp_audio_file, output_path)

        assert result.bpm == 125.0
        mock_detect.assert_not_called()

    def test_pipeline_progress_callback(
        self,
        mock_extract_vocals,
        mock_pipeline_bpm,
        temp_audio_file: Path,
        tmp_path: Path,
    ):
        """Test progress callback is called during processing."""
        output_path = tmp_path / "output_progress.wav"
        progress_calls = []

        def progress_callback(stage: str, percent: float):
            progress_calls.append((stage, percent))

        options = ProcessingOptions(progress_callback=progress_callback)
        pipeline = AcapellaPipeline(options)

        pipeline.process(temp_audio_file, output_path)

        # Should have received progress updates
        assert len(progress_calls) > 0

        # Check for expected stages
        stages = [call[0] for call in progress_calls]
        assert "Detecting BPM" in stages
        assert "Extracting vocals" in stages
        assert "Saving" in stages


class TestAcapellaPipelineDetectBPMOnly:
    """Tests for BPM-only detection."""

    def test_detect_bpm_only(self, temp_audio_file: Path, mock_pipeline_bpm):
        """Test BPM detection without vocal extraction."""
        pipeline = AcapellaPipeline()

        bpm = pipeline.detect_bpm_only(temp_audio_file)

        assert isinstance(bpm, float)
        assert bpm > 0

    def test_detect_bpm_only_accepts_string_path(
        self, temp_audio_file: Path, mock_pipeline_bpm
    ):
        """Test BPM detection accepts string path."""
        pipeline = AcapellaPipeline()

        bpm = pipeline.detect_bpm_only(str(temp_audio_file))

        assert isinstance(bpm, float)
        assert bpm > 0


class TestPipelineWithRealSilenceTrimming:
    """Tests that exercise real silence trimming with mocked vocals."""

    @pytest.fixture
    def mock_vocals_with_silence(self, mocker, sample_rate: int):
        """Mock extract_vocals to return audio with leading silence."""
        # Create vocals with 0.5s silence then 0.5s tone
        silence = np.zeros(sample_rate // 2, dtype=np.float32)
        t = np.linspace(0, 0.5, sample_rate // 2, endpoint=False)
        tone = (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)
        mono = np.concatenate([silence, tone])
        mock_vocals = np.stack([mono, mono], axis=0)

        mock = mocker.patch("acapella.core.pipeline.extract_vocals")
        mock.return_value = (mock_vocals, sample_rate)
        return mock

    def test_silence_is_trimmed(
        self,
        mock_vocals_with_silence,
        mock_pipeline_bpm,
        temp_audio_file: Path,
        tmp_path: Path,
    ):
        """Test that leading silence is actually trimmed."""
        output_path = tmp_path / "output_trimmed.wav"
        options = ProcessingOptions(
            trim_silence=True,
            silence_threshold_db=30.0,
        )
        pipeline = AcapellaPipeline(options)

        result = pipeline.process(temp_audio_file, output_path)

        # Should have trimmed some silence
        assert result.silence_trimmed_ms > 0
        # Trimmed duration should be less than original
        assert result.trimmed_duration < result.original_duration
