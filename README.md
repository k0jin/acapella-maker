# Acapella

<img width="256" height="256" alt="icon" src="https://github.com/user-attachments/assets/9de7b8a6-22a4-41db-9b33-417185aff673" /> <img width="256" height="256" alt="Screenshot 2026-01-30 at 10 44 11 PM" src="https://github.com/user-attachments/assets/d2607a98-4f0a-43e9-b768-73b14025ae73" />

Extract + download + prepare acapella samples from YouTube with local stem splitting, BPM detection, and silence trimming 



## Features

- **AI Stem Splitting** - Local + offline processing using [Demucs](https://github.com/adefossez/demucs)
- **YouTube Download** - Download and extract vocals directly from YouTube URLs using [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **BPM Detection** - Automatic tempo detection using [librosa ](https://github.com/librosa/librosa)
- **Silence Trimming** - Configurable automatic removal of leading/trailing silence
- **GUI & CLI** - Full-featured graphical interface and command-line tool
- **Cross-Platform** - Works on macOS, Windows, 


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
acapella-gui
```

Or run as a module:
```bash
python -m acapella.gui
```

### Command Line

```bash
# Extract vocals from a local file
acapella extract song.mp3

# Extract vocals from YouTube
acapella extract "https://youtube.com/watch?v=..."

# With options
acapella extract song.mp3 -o vocals.wav --silence-threshold 40

# BPM detection only
acapella bpm song.mp3
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
pyinstaller acapella_gui.spec
```

The built application will be in:
- **macOS:** `dist/Acapella.app`
- **Windows:** `dist/Acapella/Acapella.exe`

### Notes

- The first run may take longer as it downloads the Demucs AI model (~80MB)
- For fully offline builds, run the app once before building to cache the model
