# Acapella Maker

Extract acapella vocals from audio files with BPM detection and silence trimming.

## Installation

```bash
pip install -e .
```

With GUI support:
```bash
pip install -e ".[gui]"
```

**System requirements:** ffmpeg, libsndfile

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
# Extract vocals
acapella-maker extract song.mp3

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

# Build the app
pyinstaller acapella_maker_gui.spec
```

The built application will be in:
- **macOS:** `dist/Acapella Maker.app`
- **Windows:** `dist/AcapellaMaker/AcapellaMaker.exe`

### Notes

- The first run may take longer as it downloads the Demucs AI model (~80MB)
- For fully offline builds, run the app once before building to cache the model
