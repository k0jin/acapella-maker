# Acapella Maker

Extract + download acapella samples from YouTube with local stem splitting.

## Features

- **Local AI Stem Splitting** - Uses Demucs deep learning model for high-quality vocal isolation
- **YouTube Download** - Download and extract vocals directly from YouTube URLs
- **BPM Detection** - Automatic tempo detection for DJ-friendly exports
- **Silence Trimming** - Configurable automatic removal of leading/trailing silence
- **GUI & CLI** - Full-featured graphical interface and command-line tool
- **Cross-Platform** - Works on macOS, Windows, and Linux

## Requirements

- Python 3.9+
- ffmpeg
- libsndfile

## Installation

```bash
pip install -e .
```

With GUI support:
```bash
pip install -e ".[gui]"
```

## Usage

### GUI

```bash
acapella-maker-gui
```

Or run as a module:
```bash
python -m acapella_maker.gui
```

### Command Line

```bash
# Extract vocals from a local file
acapella-maker extract song.mp3

# Extract vocals from YouTube
acapella-maker extract "https://youtube.com/watch?v=..."

# With options
acapella-maker extract song.mp3 -o vocals.wav --silence-threshold 40

# BPM detection only
acapella-maker bpm song.mp3
```

## Options

- `-o, --output PATH` - Output file path (default: `<input>_acapella.wav`)
- `-s, --silence-threshold DB` - Silence threshold in dB (default: 30)
- `--no-trim` - Disable silence trimming
- `-v, --verbose` - Verbose output

## Building Standalone App

Build a standalone application using PyInstaller:

```bash
# Install build dependencies
pip install -e ".[gui,build]"

# Build the app (macOS/Linux)
./build.sh

# Or manually with PyInstaller
pyinstaller acapella_maker_gui.spec
```

The built application will be in:
- **macOS:** `dist/Acapella Maker.app`
- **Windows:** `dist/AcapellaMaker/AcapellaMaker.exe`

### Notes

- The first run may take longer as it downloads the Demucs AI model (~80MB)
- For fully offline builds, run the app once before building to cache the model
