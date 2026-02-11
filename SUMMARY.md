# Acapella Maker - Repository Summary

## Overview

**Acapella Maker** is a cross-platform desktop application and CLI tool that extracts vocal tracks from audio files using AI-powered stem separation. It downloads music from YouTube, performs vocal separation with Demucs, and processes the extracted vocals with BPM detection and silence trimming.

**Primary Use Cases:** DJ sampling, music production, and content creation.

## Tech Stack

| Category | Technology |
|----------|-----------|
| Language | Python 3.9+ |
| Build System | Hatchling |
| AI/ML | Demucs (PyTorch) for vocal/stem separation |
| Audio Analysis | librosa (BPM detection), soundfile (WAV I/O), NumPy |
| YouTube | yt-dlp |
| CLI | Typer + Rich |
| GUI | PySide6 (Qt) |
| Testing | pytest, pytest-cov, pytest-mock |
| Linting | ruff |
| Packaging | PyInstaller |

## Architecture

```
src/acapella_maker/
├── cli.py                  # CLI commands: extract, bpm, config
├── config.py               # TOML-based platform-aware configuration
├── exceptions.py           # Custom exception hierarchy
├── logging_config.py       # Logging setup
│
├── core/                   # Pure audio processing (no UI dependencies)
│   ├── pipeline.py         # Main AcapellaPipeline orchestrator
│   ├── vocal_extractor.py  # Demucs model integration
│   ├── bpm_detector.py     # librosa beat tracking
│   ├── silence_trimmer.py  # RMS-based silence removal with fade-in
│   ├── youtube.py          # yt-dlp download with context manager cleanup
│   └── audio_io.py         # Audio load/save abstraction
│
├── gui/                    # PySide6 desktop application
│   ├── main_window.py      # Main window orchestration
│   ├── colors.py           # Dark theme styling
│   ├── widgets/            # UI components (input, options, output, progress, results)
│   └── workers/            # QThread workers for non-blocking extraction
│
└── models/
    └── result.py           # ProcessingOptions and ProcessingResult dataclasses
```

## Processing Pipeline

```
Input (File or YouTube URL)
  → Download audio (yt-dlp, if YouTube)
  → Load audio (librosa)
  → Detect BPM (librosa beat tracker)
  → Extract vocals (Demucs PyTorch model)
  → Trim silence (RMS threshold + configurable fade-in)
  → Save as WAV (soundfile)
  → Output results with metadata
```

## Key Design Patterns

- **Pipeline Pattern** — `AcapellaPipeline` orchestrates sequential processing steps
- **Worker Thread Pattern** — GUI uses QThread workers to prevent UI freezing during long operations
- **Signals/Slots (Qt)** — Loose coupling between GUI widgets and processing workers
- **Custom Exception Hierarchy** — Domain-specific errors (e.g., `VocalExtractionError`)
- **Platform-Aware Configuration** — TOML config in `~/.config/acapella-maker/` (Linux/macOS) or `%APPDATA%` (Windows)
- **Context Manager Cleanup** — YouTube temp files cleaned up even on errors

## Testing

- **Unit tests** — Individual modules (audio_io, bpm_detector, silence_trimmer, youtube, etc.)
- **Integration tests** — End-to-end pipeline testing
- **CLI tests** — Command-line argument parsing and output
- **CI** — GitHub Actions runs pytest on Python 3.9-3.11 with ruff linting

## CI/CD

- **test.yml** — Automated testing across Python versions, ruff linting, Codecov coverage
- **build.yml** — Standalone executables for macOS and Windows via PyInstaller, published as GitHub Releases

## Codebase Stats

- ~1,274 lines of Python across 28+ modules
- Dual interface: CLI and GUI
- Cross-platform: macOS, Windows, Linux
